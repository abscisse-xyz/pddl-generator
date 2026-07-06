from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from pddl_dataset.runner import BatchInstanceSpec, generate_batch
from pddl_dataset.schema import Generator
from pddl_generator.batch import BATCH_SPECS
from pddl_generator.batch.citycar import (
    TOPOLOGY_RECIPES,
    derive_citycar_parameters,
    derive_instance,
    derive_instance_with_params,
)
from pddl_generator.batch.cli import main as batch_main
from pddl_generator.batch.travel import derive_travel_parameters
from pddl_problem.citycar.schema import CityCarConfig

FIXTURES = Path(__file__).parent / "fixtures"


def test_batch_specs_are_registered_for_curated_domains():
    assert {"cavediving", "citycar", "schedule", "travel"} == set(BATCH_SPECS)


def test_batch_derivation_preserves_existing_policy_shape():
    citycar = derive_citycar_parameters(index=0, count=200, seed_base=10)
    assert citycar == {
        "family": "compact_clear",
        "rows": 3,
        "columns": 3,
        "cars": 2,
        "garages": 1,
        "roads": 3,
        "density": 1.0,
        "mode": "current",
        "topology_family": "auto",
        "seed": 10,
    }

    citycar_solution = derive_citycar_parameters(index=10, count=40, seed_base=10, mode="solution-first")
    assert citycar_solution["mode"] == "solution-first"
    assert citycar_solution["garages"] == 3
    assert citycar_solution["cars"] in {3, 4, 5}
    assert citycar_solution["roads"] in {5, 6}
    assert citycar_solution["rows"] <= 5
    assert citycar_solution["columns"] <= 5

    travel = derive_travel_parameters(index=1, count=4, seed_base=20)
    assert travel["family"] == "sparse_bidirectional"
    assert travel["bidirectional"] is True
    assert travel["seed"] == 21


def test_citycar_batch_derivation_covers_legacy_and_small_mode_families():
    legacy_families = [derive_citycar_parameters(index=i, count=25, seed_base=1) for i in range(5)]

    assert [params["family"] for params in legacy_families] == [
        "compact_clear",
        "compact_sparse",
        "wide_commuter",
        "tall_commuter",
        "large_busy",
    ]
    assert legacy_families[-1]["rows"] > legacy_families[0]["rows"]

    late = derive_citycar_parameters(index=9, count=10, seed_base=1, mode="solution-first")

    assert late["cars"] == 5
    assert late["roads"] == 6


def test_citycar_topology_first_uses_recipe_cycle_with_diverse_counts():
    derived = [
        derive_citycar_parameters(index=index, count=len(TOPOLOGY_RECIPES), seed_base=20, mode="topology-first")
        for index in range(len(TOPOLOGY_RECIPES))
    ]
    expected_shapes = [
        ("easy", "balanced", 3, 4, 2, 2, 5, "parallel_lanes", False),
        ("easy", "balanced", 4, 4, 2, 3, 5, "open_grid", True),
        ("easy", "balanced", 4, 4, 3, 2, 5, "diagonal_mix", False),
        ("medium", "balanced", 4, 5, 3, 3, 5, "three_spokes", False),
        ("medium", "balanced", 5, 4, 3, 4, 6, "ring_with_spurs", True),
        ("medium", "balanced", 5, 4, 4, 3, 6, "parallel_lanes", False),
        ("hard", "balanced", 5, 5, 4, 4, 6, "blocked_center", False),
        ("hard", "balanced", 5, 5, 5, 3, 6, "rooms_and_doors", False),
        ("hard", "balanced", 5, 5, 5, 4, 7, "diagonal_mix", False),
        ("easy", "road_rich", 4, 4, 2, 2, 7, "open_grid", False),
        ("easy", "junction_open", 5, 5, 2, 3, 6, "ring_with_spurs", True),
        ("medium", "car_pressure", 4, 4, 5, 2, 5, "parallel_lanes", False),
        ("medium", "garage_rich", 4, 5, 3, 5, 6, "three_spokes", True),
        ("medium", "junction_tight", 3, 4, 4, 2, 5, "diagonal_mix", False),
        ("hard", "car_pressure", 5, 4, 6, 3, 6, "rooms_and_doors", False),
        ("hard", "road_pressure", 5, 5, 5, 5, 6, "blocked_center", False),
        ("hard", "road_rich", 5, 5, 3, 3, 8, "diagonal_mix", False),
    ]

    for recipe, params, expected in zip(TOPOLOGY_RECIPES, derived, expected_shapes, strict=True):
        difficulty, profile, rows, columns, cars, garages, roads, topology_family, unused_garages = expected
        assert recipe["difficulty"] == difficulty
        assert recipe["profile"] == profile
        assert recipe["unused_garages"] is unused_garages
        assert params["family"] == f"topology-first_{difficulty}_{profile}_{topology_family}"
        assert params["rows"] == rows
        assert params["columns"] == columns
        assert params["cars"] == cars
        assert params["garages"] == garages
        assert params["roads"] == roads
        assert params["topology_family"] == topology_family
        assert (params["cars"] < params["garages"]) is unused_garages

    assert {params["cars"] for params in derived} == {2, 3, 4, 5, 6}
    assert {params["garages"] for params in derived} == {2, 3, 4, 5}
    assert {params["roads"] for params in derived} == {5, 6, 7, 8}
    assert {int(params["rows"]) * int(params["columns"]) for params in derived} == {12, 16, 20, 25}
    assert any(params["cars"] < params["garages"] for params in derived)
    assert any(int(params["cars"]) > int(params["roads"]) - 1 for params in derived)
    assert any(int(params["roads"]) >= int(params["cars"]) + 4 for params in derived)
    assert any(int(params["rows"]) * int(params["columns"]) <= 12 and int(params["cars"]) >= 4 for params in derived)
    assert any(int(params["rows"]) * int(params["columns"]) >= 25 and int(params["cars"]) <= 3 for params in derived)

    for params in derived:
        junctions = int(params["rows"]) * int(params["columns"])
        assert params["mode"] == "topology-first"
        assert int(params["roads"]) >= max(4, int(params["garages"]))
        assert 2 <= int(params["garages"]) <= 5
        assert 2 <= int(params["cars"]) <= 6
        assert 12 <= junctions <= 25
        CityCarConfig.model_validate({key: params[key] for key in CityCarConfig.model_fields if key in params})


def test_citycar_topology_first_recipe_selection_cycles_for_large_batches():
    first = derive_citycar_parameters(index=0, count=20, seed_base=5, mode="topology-first")
    cycled = derive_citycar_parameters(index=len(TOPOLOGY_RECIPES), count=20, seed_base=5, mode="topology-first")

    assert first["family"] == cycled["family"]
    assert first["rows"] == cycled["rows"]
    assert first["columns"] == cycled["columns"]
    assert first["cars"] == cycled["cars"]
    assert first["garages"] == cycled["garages"]
    assert first["roads"] == cycled["roads"]
    assert first["seed"] == 5
    assert cycled["seed"] == 5 + len(TOPOLOGY_RECIPES)


def test_citycar_batch_derivation_rejects_unknown_mode():
    with pytest.raises(ValueError, match="mode must be one of"):
        derive_citycar_parameters(index=0, count=1, seed_base=1, mode="solution1")


def test_citycar_batch_instance_helpers_preserve_family_seed_and_overrides():
    default_instance = derive_instance(index=0, count=1, seed_base=4)
    assert default_instance.family == "compact_clear"
    assert default_instance.seed == 4

    overridden = derive_instance_with_params(
        index=0,
        count=1,
        seed_base=4,
        overrides={"mode": "solution-first", "cars": 5},
    )
    assert overridden.family == "solution-first_open_grid"
    assert overridden.seed == 4
    assert overridden.params["mode"] == "solution-first"
    assert overridden.params["cars"] == 5


def test_generate_batch_records_plan_family_and_per_instance_params(tmp_path):
    gen_dir = tmp_path / "gen_dir"
    gen_dir.mkdir()
    target = gen_dir / "gen"
    target.write_text((FIXTURES / "fake_stdout_gen.py").read_text())
    target.chmod(0o755)
    (gen_dir / "domain.pddl").write_text("(define (domain fake))\n")
    out_dir = tmp_path / "out"

    gen = Generator.model_validate(
        {
            "name": "fake-batch",
            "binary": sys.executable,
            "fixed_args": [str(target)],
            "domain_file": {"source": "static", "path": "domain.pddl"},
            "output": {"mode": "stdout"},
            "parameters": [
                {"name": "balls", "type": "int", "flag": "-n", "required": True},
                {"name": "seed", "type": "int", "flag": "--seed"},
            ],
        }
    )

    result = generate_batch(
        gen,
        gen_dir,
        out_dir,
        [
            BatchInstanceSpec(params={"balls": 2, "seed": 7}, family="small", seed=7),
            BatchInstanceSpec(params={"balls": 3, "seed": 8}, family="large", seed=8),
        ],
        plan={"families": ["small", "large"]},
    )

    assert [instance.file for instance in result.instances] == ["p01.pddl", "p02.pddl"]
    assert (out_dir / "domain.pddl").exists()
    assert (out_dir / "p01.pddl").exists()
    manifest = json.loads((out_dir / "manifest.json").read_text())
    assert manifest["plan"] == {"families": ["small", "large"]}
    assert manifest["instances"][0]["family"] == "small"
    assert manifest["instances"][0]["seed"] == 7
    assert manifest["instances"][0]["params"] == {"balls": 2, "seed": 7}
    assert "-n" in manifest["instances"][0]["command"]


def test_batch_cli_generates_citycar_with_param_overrides(tmp_path: Path) -> None:
    out_dir = tmp_path / "citycar-batch"

    exit_code = batch_main(
        [
            "citycar",
            "--out",
            str(out_dir),
            "--count",
            "2",
            "--seed-base",
            "9",
            "-p",
            "mode=topology-first",
        ]
    )

    assert exit_code == 0
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert [instance["params"]["mode"] for instance in manifest["instances"]] == [
        "topology-first",
        "topology-first",
    ]


def test_batch_cli_reports_user_errors(capsys) -> None:
    assert batch_main(["--list"]) == 0
    assert "citycar" in capsys.readouterr().out

    assert batch_main(["missing-domain"]) == 2
    assert "unknown batch domain" in capsys.readouterr().err

    assert batch_main(["citycar", "--count", "-1"]) == 2
    assert "--count must be non-negative" in capsys.readouterr().err

    assert batch_main(["citycar", "-p", "broken"]) == 2
    assert "--param expects NAME=VALUE" in capsys.readouterr().err

    assert batch_main(["citycar", "-p", "mode=solution1"]) == 2
    assert "mode must be one of" in capsys.readouterr().err

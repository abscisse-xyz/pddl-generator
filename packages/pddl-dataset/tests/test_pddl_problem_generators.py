from __future__ import annotations

import random
from pathlib import Path

import pytest
from pddl_problem.citycar.generator import _topology_mask
from pddl_problem.citycar.generator import generate_problem as generate_citycar_problem
from pddl_problem.citycar.generator_cmd_line import main as citycar_main
from pddl_problem.citycar.schema import CityCarConfig
from pddl_problem.common import parse_bool, positive_int
from pddl_problem.logistic.generator import generate_problem as generate_logistic_problem
from pddl_problem.logistic.generator_cmd_line import main as logistic_main
from pddl_problem.logistic.schema import LogisticConfig
from pddl_problem.travel.generator import generate_problem as generate_travel_problem
from pddl_problem.travel.generator_cmd_line import main as travel_main
from pddl_problem.travel.schema import TravelConfig
from pydantic import ValidationError


def test_citycar_config_rejects_invalid_solution_mode_shapes() -> None:
    with pytest.raises(ValidationError, match="garages must fit"):
        CityCarConfig(rows=2, columns=2, garages=5)

    with pytest.raises(ValidationError, match="at least two garages"):
        CityCarConfig(mode="topology-first", garages=1)

    with pytest.raises(ValidationError, match="at least three garages"):
        CityCarConfig(mode="solution-first", garages=2)

    with pytest.raises(ValidationError, match="at least five roads"):
        CityCarConfig(mode="solution-first", garages=3, roads=3)

    with pytest.raises(ValidationError):
        CityCarConfig(mode="solution1")


def test_citycar_current_mode_uses_density_style_generation() -> None:
    config = CityCarConfig(
        problem_name="citycar_current",
        rows=3,
        columns=3,
        cars=2,
        garages=1,
        roads=3,
        density=0.45,
        mode="current",
        seed=5,
    )

    problem = generate_citycar_problem(config)

    assert "(define (problem citycar_current)" in problem.problem_pddl
    assert "garage0 - garage" in problem.problem_pddl
    assert "(starting car0 garage0)" in problem.problem_pddl
    assert "(arrived car1" in problem.problem_pddl


def test_citycar_default_problem_name_reflects_instance_shape() -> None:
    config = CityCarConfig(
        rows=4,
        columns=4,
        cars=3,
        garages=3,
        roads=5,
        mode="topology-first",
        topology_family="parallel_lanes",
        seed=42,
    )

    problem = generate_citycar_problem(config)

    assert problem.name.startswith("citycar-topology-first-parallel-lanes-4x4-c3-g3-r5")
    assert problem.name.endswith("-s42")
    assert f"(define (problem {problem.name})" in problem.problem_pddl


def test_citycar_topology_first_can_emit_unused_garages() -> None:
    config = CityCarConfig(
        rows=4,
        columns=4,
        cars=2,
        garages=3,
        roads=5,
        mode="topology-first",
        topology_family="open_grid",
        seed=2,
    )

    problem = generate_citycar_problem(config)

    assert "garage0 garage1 garage2 - garage" in problem.problem_pddl
    assert "(at_garage garage2" in problem.problem_pddl
    assert "(starting car0 garage0)" in problem.problem_pddl
    assert "(starting car1 garage1)" in problem.problem_pddl
    assert "garage2)" not in "\n".join(
        line for line in problem.problem_pddl.splitlines() if line.startswith("(starting")
    )
    garage_junctions = {
        line.split()[-1].rstrip(")") for line in problem.problem_pddl.splitlines() if line.startswith("(at_garage")
    }
    goal_junctions = {
        line.split()[-1].rstrip(")") for line in problem.problem_pddl.splitlines() if line.startswith("(arrived")
    }
    assert garage_junctions.isdisjoint(goal_junctions)
    assert "-c2-g3-" in problem.name


def test_citycar_solution_modes_are_deterministic_and_small() -> None:
    config = CityCarConfig(
        problem_name="citycar_seeded",
        rows=5,
        columns=5,
        cars=5,
        garages=3,
        roads=6,
        mode="solution-first",
        seed=17,
    )

    first = generate_citycar_problem(config)
    second = generate_citycar_problem(config)

    assert first.problem_pddl == second.problem_pddl
    assert "(define (problem citycar_seeded)" in first.problem_pddl
    assert "garage0 garage1 garage2 - garage" in first.problem_pddl
    assert "road0 road1 road2 road3 road4 road5 - road" in first.problem_pddl
    assert "(arrived car4" in first.problem_pddl


@pytest.mark.parametrize(
    "family",
    [
        "open_grid",
        "parallel_lanes",
        "ring_with_spurs",
        "three_spokes",
        "rooms_and_doors",
        "blocked_center",
        "diagonal_mix",
        "seeded_sparse",
    ],
)
def test_citycar_topology_masks_are_nonempty_and_bounded(family: str) -> None:
    mask = _topology_mask(5, 5, family, random.Random(3))

    assert mask
    assert mask <= {(r, c) for r in range(5) for c in range(5)}


def test_citycar_topology_first_falls_back_to_solution_first_when_no_route_exists() -> None:
    config = CityCarConfig(
        problem_name="citycar_fallback",
        rows=4,
        columns=4,
        cars=3,
        garages=3,
        roads=5,
        mode="topology-first",
        topology_family="seeded_sparse",
        seed=12,
    )

    problem = generate_citycar_problem(config)

    assert "(define (problem citycar_fallback)" in problem.problem_pddl
    assert "garage0 garage1 garage2 - garage" in problem.problem_pddl


def test_citycar_cli_writes_domain_and_problem_files(tmp_path: Path) -> None:
    domain_path = tmp_path / "citycar-domain.pddl"
    problem_path = tmp_path / "citycar-problem.pddl"

    exit_code = citycar_main(
        [
            "-domain_file",
            str(domain_path),
            "-problem_file",
            str(problem_path),
            "-problem_name",
            "citycar_cli",
            "-rows",
            "4",
            "-columns",
            "4",
            "-cars",
            "3",
            "-garages",
            "3",
            "-roads",
            "5",
            "-mode",
            "topology-first",
            "-seed",
            "3",
        ]
    )

    assert exit_code == 0
    assert domain_path.read_text(encoding="utf-8").startswith("(define (domain citycar)")
    body = problem_path.read_text(encoding="utf-8")
    assert "(define (problem citycar_cli)" in body
    assert "(starting car0 garage0)" in body
    assert "(= (total-cost) 0)" in body


def test_common_validation_helpers_reject_bad_values() -> None:
    assert parse_bool("false") is False
    assert parse_bool("Y") is True

    with pytest.raises(ValueError, match="positive"):
        positive_int("0")
    with pytest.raises(ValueError, match="boolean"):
        parse_bool("maybe")


def test_travel_config_rejects_impossible_shortcut_count() -> None:
    with pytest.raises(ValidationError, match="extra_edges"):
        TravelConfig(locations=4, extra_edges=4)


def test_travel_generation_is_deterministic_for_seed() -> None:
    config = TravelConfig(problem_name="travel_seeded", locations=6, extra_edges=3, seed=7, bidirectional=True)

    first = generate_travel_problem(config)
    second = generate_travel_problem(config)

    assert first.problem_pddl == second.problem_pddl
    assert "travel_domain" in first.problem_pddl
    assert "(is_at l1)" in first.problem_pddl
    assert "(is_at l6)" in first.problem_pddl
    assert "(= (total_travel_time) 0)" in first.problem_pddl


def test_travel_cli_writes_domain_and_problem_files(tmp_path: Path) -> None:
    domain_path = tmp_path / "travel-domain.pddl"
    problem_path = tmp_path / "travel-problem.pddl"

    exit_code = travel_main(
        [
            "-domain_file",
            str(domain_path),
            "-problem_file",
            str(problem_path),
            "-problem_name",
            "travel_cli",
            "-locations",
            "5",
            "-extra_edges",
            "2",
            "-seed",
            "3",
            "-bidirectional",
            "True",
        ]
    )

    assert exit_code == 0
    assert domain_path.read_text(encoding="utf-8").startswith("(define (domain travel_domain)")
    body = problem_path.read_text(encoding="utf-8")
    assert "(define (problem travel_cli)" in body
    assert "(is_connected l1 l2)" in body


def test_logistic_config_rejects_invalid_ranges() -> None:
    with pytest.raises(ValidationError, match="max_distance"):
        LogisticConfig(min_distance=10, max_distance=5)


def test_logistic_generation_is_deterministic_for_seed() -> None:
    config = LogisticConfig(problem_name="logistic_seeded", locations=5, robots=3, packages=4, seed=11)

    first = generate_logistic_problem(config)
    second = generate_logistic_problem(config)

    assert first.problem_pddl == second.problem_pddl
    assert "logistic_domain" in first.problem_pddl
    assert "(robot_free r1)" in first.problem_pddl
    assert "(package_at p4 l1)" in first.problem_pddl
    assert "(package_at p4 l5)" in first.problem_pddl


def test_logistic_cli_writes_domain_and_problem_files(tmp_path: Path) -> None:
    domain_path = tmp_path / "logistic-domain.pddl"
    problem_path = tmp_path / "logistic-problem.pddl"

    exit_code = logistic_main(
        [
            "-domain_file",
            str(domain_path),
            "-problem_file",
            str(problem_path),
            "-problem_name",
            "logistic_cli",
            "-locations",
            "4",
            "-robots",
            "2",
            "-packages",
            "2",
            "-seed",
            "5",
        ]
    )

    assert exit_code == 0
    assert domain_path.read_text(encoding="utf-8").startswith("(define (domain logistic_domain)")
    body = problem_path.read_text(encoding="utf-8")
    assert "(define (problem logistic_cli)" in body
    assert "(robot_at r1 l1)" in body
    assert "(package_at p2 l4)" in body

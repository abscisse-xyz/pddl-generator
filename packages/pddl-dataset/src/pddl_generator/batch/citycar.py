from __future__ import annotations

from pddl_dataset.runner import BatchInstanceSpec

from pddl_generator.batch.base import BatchSpec, build_instance, interp_int

FAMILIES = [
    "compact_clear",
    "compact_sparse",
    "wide_commuter",
    "tall_commuter",
    "large_busy",
]

TOPOLOGY_FAMILIES = [
    "open_grid",
    "parallel_lanes",
    "ring_with_spurs",
    "three_spokes",
    "rooms_and_doors",
    "blocked_center",
    "diagonal_mix",
]

TOPOLOGY_RECIPES = [
    {
        "difficulty": "easy",
        "profile": "balanced",
        "rows": 3,
        "columns": 4,
        "cars": 2,
        "garages": 2,
        "roads": 5,
        "topology_family": "parallel_lanes",
        "unused_garages": False,
    },
    {
        "difficulty": "easy",
        "profile": "balanced",
        "rows": 4,
        "columns": 4,
        "cars": 2,
        "garages": 3,
        "roads": 5,
        "topology_family": "open_grid",
        "unused_garages": True,
    },
    {
        "difficulty": "easy",
        "profile": "balanced",
        "rows": 4,
        "columns": 4,
        "cars": 3,
        "garages": 2,
        "roads": 5,
        "topology_family": "diagonal_mix",
        "unused_garages": False,
    },
    {
        "difficulty": "medium",
        "profile": "balanced",
        "rows": 4,
        "columns": 5,
        "cars": 3,
        "garages": 3,
        "roads": 5,
        "topology_family": "three_spokes",
        "unused_garages": False,
    },
    {
        "difficulty": "medium",
        "profile": "balanced",
        "rows": 5,
        "columns": 4,
        "cars": 3,
        "garages": 4,
        "roads": 6,
        "topology_family": "ring_with_spurs",
        "unused_garages": True,
    },
    {
        "difficulty": "medium",
        "profile": "balanced",
        "rows": 5,
        "columns": 4,
        "cars": 4,
        "garages": 3,
        "roads": 6,
        "topology_family": "parallel_lanes",
        "unused_garages": False,
    },
    {
        "difficulty": "hard",
        "profile": "balanced",
        "rows": 5,
        "columns": 5,
        "cars": 4,
        "garages": 4,
        "roads": 6,
        "topology_family": "blocked_center",
        "unused_garages": False,
    },
    {
        "difficulty": "hard",
        "profile": "balanced",
        "rows": 5,
        "columns": 5,
        "cars": 5,
        "garages": 3,
        "roads": 6,
        "topology_family": "rooms_and_doors",
        "unused_garages": False,
    },
    {
        "difficulty": "hard",
        "profile": "balanced",
        "rows": 5,
        "columns": 5,
        "cars": 5,
        "garages": 4,
        "roads": 7,
        "topology_family": "diagonal_mix",
        "unused_garages": False,
    },
    {
        "difficulty": "easy",
        "profile": "road_rich",
        "rows": 4,
        "columns": 4,
        "cars": 2,
        "garages": 2,
        "roads": 7,
        "topology_family": "open_grid",
        "unused_garages": False,
    },
    {
        "difficulty": "easy",
        "profile": "junction_open",
        "rows": 5,
        "columns": 5,
        "cars": 2,
        "garages": 3,
        "roads": 6,
        "topology_family": "ring_with_spurs",
        "unused_garages": True,
    },
    {
        "difficulty": "medium",
        "profile": "car_pressure",
        "rows": 4,
        "columns": 4,
        "cars": 5,
        "garages": 2,
        "roads": 5,
        "topology_family": "parallel_lanes",
        "unused_garages": False,
    },
    {
        "difficulty": "medium",
        "profile": "garage_rich",
        "rows": 4,
        "columns": 5,
        "cars": 3,
        "garages": 5,
        "roads": 6,
        "topology_family": "three_spokes",
        "unused_garages": True,
    },
    {
        "difficulty": "medium",
        "profile": "junction_tight",
        "rows": 3,
        "columns": 4,
        "cars": 4,
        "garages": 2,
        "roads": 5,
        "topology_family": "diagonal_mix",
        "unused_garages": False,
    },
    {
        "difficulty": "hard",
        "profile": "car_pressure",
        "rows": 5,
        "columns": 4,
        "cars": 6,
        "garages": 3,
        "roads": 6,
        "topology_family": "rooms_and_doors",
        "unused_garages": False,
    },
    {
        "difficulty": "hard",
        "profile": "road_pressure",
        "rows": 5,
        "columns": 5,
        "cars": 5,
        "garages": 5,
        "roads": 6,
        "topology_family": "blocked_center",
        "unused_garages": False,
    },
    {
        "difficulty": "hard",
        "profile": "road_rich",
        "rows": 5,
        "columns": 5,
        "cars": 3,
        "garages": 3,
        "roads": 8,
        "topology_family": "diagonal_mix",
        "unused_garages": False,
    },
]

PLAN = {
    "mode_parameter": "mode chooses current, topology-first, or solution-first",
    "current_size_progression": "legacy density-style grid size increases roughly linearly from 3 to 12",
    "current_families": FAMILIES,
    "topology_families": TOPOLOGY_FAMILIES,
    "topology_recipes": TOPOLOGY_RECIPES,
    "small_mode_size_policy": (
        "topology-first is recipe-driven from 3x4 through 5x5; solution-first stays 4x4 through 5x5"
    ),
    "small_mode_traffic_policy": (
        "topology-first varies 2-6 cars, 2-5 garages, and 5-8 roads across mixed pressure profiles; "
        "solution-first keeps 3 garages, 3-5 cars, and 5-6 road objects"
    ),
    "execution": "instances are generated in-process by the pddl-dataset runner",
}


def derive_citycar_parameters(index: int, count: int, seed_base: int, mode: str = "current") -> dict[str, object]:
    normalized_mode = _normalize_mode(mode)
    if normalized_mode == "topology-first":
        return _derive_topology_first_citycar_parameters(index, seed_base)
    if normalized_mode == "solution-first":
        return _derive_solution_citycar_parameters(index, count, seed_base)
    if normalized_mode != "current":
        raise ValueError("mode must be one of: current, topology-first, solution-first")
    return _derive_current_citycar_parameters(index, count, seed_base)


def _derive_current_citycar_parameters(index: int, count: int, seed_base: int) -> dict[str, object]:
    progress = 0.0 if count <= 1 else index / (count - 1)
    family = index % 5
    base = interp_int(3, 12, progress)

    if family == 0:
        rows = base
        columns = base
        car_bonus = 0
        density_start, density_end = 1.0, 0.90
    elif family == 1:
        rows = base
        columns = base + 1
        car_bonus = 1
        density_start, density_end = 0.88, 0.62
    elif family == 2:
        rows = max(3, base - 1)
        columns = base + 3
        car_bonus = 2
        density_start, density_end = 0.95, 0.76
    elif family == 3:
        rows = base + 2
        columns = max(3, base - 1)
        car_bonus = 2
        density_start, density_end = 0.95, 0.76
    else:
        rows = base + 2
        columns = base + 2
        car_bonus = 3
        density_start, density_end = 0.82, 0.55

    garages = min(columns, interp_int(1, 4, progress) + (1 if family in (2, 4) and progress > 0.45 else 0))
    cars = max(1, interp_int(2, 12, progress) + car_bonus)
    density = round(density_start + (density_end - density_start) * progress, 2)

    return {
        "family": FAMILIES[family],
        "rows": rows,
        "columns": columns,
        "cars": cars,
        "garages": garages,
        "roads": cars + garages,
        "density": density,
        "mode": "current",
        "topology_family": "auto",
        "seed": seed_base + index,
    }


def _derive_topology_first_citycar_parameters(index: int, seed_base: int) -> dict[str, object]:
    recipe = TOPOLOGY_RECIPES[index % len(TOPOLOGY_RECIPES)]
    difficulty = str(recipe["difficulty"])
    profile = str(recipe["profile"])
    topology_family = str(recipe["topology_family"])

    return {
        "family": f"topology-first_{difficulty}_{profile}_{topology_family}",
        "rows": int(recipe["rows"]),
        "columns": int(recipe["columns"]),
        "cars": int(recipe["cars"]),
        "garages": int(recipe["garages"]),
        "roads": int(recipe["roads"]),
        "density": 1.0,
        "mode": "topology-first",
        "topology_family": topology_family,
        "seed": seed_base + index,
    }


def _derive_solution_citycar_parameters(index: int, count: int, seed_base: int) -> dict[str, object]:
    progress = 0.0 if count <= 1 else index / (count - 1)
    family = TOPOLOGY_FAMILIES[index % len(TOPOLOGY_FAMILIES)]

    if progress < 0.25:
        rows, columns = 4, 4
        cars, roads = 3, 5
    elif progress < 0.65:
        rows, columns = (4, 5) if index % 2 == 0 else (5, 4)
        cars, roads = 4, 5 + (index % 2)
    else:
        rows, columns = 5, 5
        cars, roads = 5, 6

    if family in {"ring_with_spurs", "blocked_center", "rooms_and_doors"}:
        rows = max(rows, 5)
        columns = max(columns, 5)
    return {
        "family": f"solution-first_{family}",
        "rows": rows,
        "columns": columns,
        "cars": cars,
        "garages": 3,
        "roads": roads,
        "density": 1.0,
        "mode": "solution-first",
        "topology_family": family,
        "seed": seed_base + index,
    }


def derive_instance(index: int, count: int, seed_base: int) -> BatchInstanceSpec:
    return build_instance(derive_citycar_parameters(index, count, seed_base))


def derive_instance_with_params(
    index: int,
    count: int,
    seed_base: int,
    overrides: dict[str, object],
) -> BatchInstanceSpec:
    mode = str(overrides.get("mode", "current"))
    params = derive_citycar_parameters(index, count, seed_base, mode=mode)
    params.update(overrides)
    return build_instance(params)


def _normalize_mode(mode: str) -> str:
    return mode.strip().lower()


SPEC = BatchSpec(
    domain="citycar",
    default_count=200,
    plan=PLAN,
    derive=derive_instance,
    derive_with_params=derive_instance_with_params,
)

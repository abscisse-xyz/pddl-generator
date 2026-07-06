from __future__ import annotations

from pddl_dataset.runner import BatchInstanceSpec

from pddl_generator.batch.base import BatchSpec, build_instance, interp_int

FAMILIES = [
    "sparse_directed_corridor",
    "sparse_bidirectional",
    "medium_directed",
    "dense_bidirectional",
]

PLAN = {
    "size_progression": "locations increase roughly linearly from 5 to 30 across the batch",
    "families": FAMILIES,
    "shortcut_policy": "extra_edges are derived from family density times the available forward shortcuts",
    "cost_policy": "travel-time ranges widen with progress and shift modestly by family",
    "execution": "instances are generated in-process by the pddl-dataset runner",
}


def derive_travel_parameters(index: int, count: int, seed_base: int) -> dict[str, object]:
    progress = 0.0 if count <= 1 else index / (count - 1)
    family = index % 4

    locations = interp_int(5, 30, progress)
    max_shortcuts = (locations - 1) * (locations - 2) // 2

    density_start = [0.00, 0.08, 0.20, 0.35][family]
    density_end = [0.10, 0.18, 0.32, 0.55][family]
    density = density_start + (density_end - density_start) * progress
    extra_edges = min(max_shortcuts, round(max_shortcuts * density))

    min_travel_time = [5, 10, 15, 20][family] + round(progress * 10)
    width = interp_int(20, 120, progress)
    max_travel_time = min_travel_time + width

    return {
        "family": FAMILIES[family],
        "locations": locations,
        "extra_edges": extra_edges,
        "min_travel_time": min_travel_time,
        "max_travel_time": max_travel_time,
        "bidirectional": family in (1, 3),
        "seed": seed_base + index,
    }


def derive_instance(index: int, count: int, seed_base: int) -> BatchInstanceSpec:
    return build_instance(derive_travel_parameters(index, count, seed_base))


SPEC = BatchSpec(domain="travel", default_count=200, plan=PLAN, derive=derive_instance)

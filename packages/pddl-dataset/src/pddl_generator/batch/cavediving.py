from __future__ import annotations

from pddl_dataset.runner import BatchInstanceSpec

from pddl_generator.batch.base import BatchSpec, build_instance, interp_int

FAMILIES = [
    "single_branch_probe",
    "balanced_two_branch",
    "skewed_two_branch",
    "three_branch_dual_objective",
    "three_branch_full_objective",
]

PLAN = {
    "depth_progression": "branch depths increase roughly linearly from 3 to 8 across the batch",
    "families": FAMILIES,
    "objective_policy": "objective depths are selected from the deepest branch leaves of the current cave shape",
    "support_policy": (
        "tank/diver adjustments stay close to baseline while incompatibility density ramps from low to moderate"
    ),
    "execution": "instances are generated in-process by the pddl-dataset runner",
}


def derive_cavediving_parameters(index: int, count: int, seed_base: int) -> dict[str, object]:
    progress = 0.0 if count <= 1 else index / (count - 1)
    family = index % 5
    depth = interp_int(3, 8, progress)

    if family == 0:
        branches = [depth]
        objective_count = 1
    elif family == 1:
        branches = [depth, depth]
        objective_count = 1
    elif family == 2:
        branches = [max(2, depth - 1), depth + 1]
        objective_count = 1
    elif family == 3:
        branches = [max(2, depth - 1), depth, depth + 1]
        objective_count = 2
    else:
        branches = [depth, depth + 1, depth + 2]
        objective_count = 3

    objectives = sorted(sorted(branches, reverse=True)[:objective_count])
    neg_link_prob = round(min(0.6, 0.12 + 0.38 * progress + 0.03 * family), 2)

    tank_adjustments = [0, 0, 1, 1, 2]
    diver_adjustments = [0, 0, 0, 1, 1]
    minimum_hiring_cost = 10 + 5 * family
    maximum_hiring_cost = minimum_hiring_cost + 80 + 5 * family
    other_action_cost = round(1.0 + 0.4 * progress + 0.1 * family, 2)

    return {
        "family": FAMILIES[family],
        "cave_branches": branches,
        "objectives": objectives,
        "num_tank_adjustment": tank_adjustments[family],
        "num_diver_adjustment": diver_adjustments[family],
        "neg_link_prob": neg_link_prob,
        "minimum_hiring_cost": minimum_hiring_cost,
        "maximum_hiring_cost": maximum_hiring_cost,
        "other_action_cost": other_action_cost,
        "order_tanks": family in (0, 2, 4),
        "seed": seed_base + index,
    }


def derive_instance(index: int, count: int, seed_base: int) -> BatchInstanceSpec:
    return build_instance(derive_cavediving_parameters(index, count, seed_base))


SPEC = BatchSpec(domain="cavediving", default_count=200, plan=PLAN, derive=derive_instance)

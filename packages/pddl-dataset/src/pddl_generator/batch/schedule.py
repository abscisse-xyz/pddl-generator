from __future__ import annotations

from pddl_dataset.runner import BatchInstanceSpec

from pddl_generator.batch.base import BatchSpec, build_instance, interp_int

FAMILIES = [
    "small_colour_finish",
    "shape_heavy",
    "hole_heavy",
    "mixed_shop",
    "full_feature_shop",
]

PLAN = {
    "size_progression": "parts increase roughly linearly from 1 to the high 60s across the batch",
    "families": FAMILIES,
    "vocabulary_policy": "attribute vocabularies widen by family and progress within generator limits",
    "probability_policy": (
        "goal requirements become denser with progress, while family choice emphasizes colour, shape, or holes"
    ),
    "execution": "instances are generated in-process by the pddl-dataset runner",
}


def derive_schedule_parameters(index: int, count: int, seed_base: int) -> dict[str, object]:
    progress = 0.0 if count <= 1 else index / (count - 1)
    family = index % 5

    parts = interp_int(1, 60, progress) + [0, 2, 4, 6, 8][family]
    shapes = [0, 2, 1, 2, 2][family]
    colours = min(4, [1, 2, 2, 3, 4][family] + (1 if progress > 0.65 and family < 4 else 0))
    widths = min(3, [1, 1, 3, 2, 3][family] + (1 if progress > 0.75 and family in (0, 1) else 0))
    orientations = 1 if family in (0, 1) and progress < 0.55 else 2

    family_probs = [
        {
            "prob_g_cylindrical": (35, 55),
            "prob_i_colour": (20, 45),
            "prob_g_colour": (60, 85),
            "prob_i_hole": (5, 20),
            "prob_g_hole": (10, 25),
            "prob_g_surface": (20, 45),
        },
        {
            "prob_g_cylindrical": (70, 95),
            "prob_i_colour": (20, 40),
            "prob_g_colour": (30, 55),
            "prob_i_hole": (10, 30),
            "prob_g_hole": (20, 45),
            "prob_g_surface": (35, 65),
        },
        {
            "prob_g_cylindrical": (45, 70),
            "prob_i_colour": (15, 35),
            "prob_g_colour": (25, 50),
            "prob_i_hole": (45, 70),
            "prob_g_hole": (70, 95),
            "prob_g_surface": (25, 55),
        },
        {
            "prob_g_cylindrical": (55, 85),
            "prob_i_colour": (35, 60),
            "prob_g_colour": (55, 85),
            "prob_i_hole": (35, 60),
            "prob_g_hole": (55, 85),
            "prob_g_surface": (45, 75),
        },
        {
            "prob_g_cylindrical": (70, 100),
            "prob_i_colour": (45, 70),
            "prob_g_colour": (70, 100),
            "prob_i_hole": (45, 70),
            "prob_g_hole": (70, 100),
            "prob_g_surface": (60, 95),
        },
    ][family]

    params: dict[str, object] = {
        "family": FAMILIES[family],
        "parts": parts,
        "shapes": shapes,
        "colours": colours,
        "widths": widths,
        "orientations": orientations,
        "seed": seed_base + index,
    }

    for name, (start, end) in family_probs.items():
        params[name] = interp_int(start, end, progress)

    return params


def derive_instance(index: int, count: int, seed_base: int) -> BatchInstanceSpec:
    return build_instance(derive_schedule_parameters(index, count, seed_base))


SPEC = BatchSpec(domain="schedule", default_count=200, plan=PLAN, derive=derive_instance)

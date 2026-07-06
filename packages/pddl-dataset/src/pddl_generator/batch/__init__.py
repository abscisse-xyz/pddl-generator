"""Curated batch-generation plans."""

from pddl_generator.batch.base import BatchSpec
from pddl_generator.batch.cavediving import SPEC as CAVEDIVING_SPEC
from pddl_generator.batch.citycar import SPEC as CITYCAR_SPEC
from pddl_generator.batch.schedule import SPEC as SCHEDULE_SPEC
from pddl_generator.batch.travel import SPEC as TRAVEL_SPEC

BATCH_SPECS: dict[str, BatchSpec] = {
    spec.domain: spec
    for spec in (
        CAVEDIVING_SPEC,
        CITYCAR_SPEC,
        SCHEDULE_SPEC,
        TRAVEL_SPEC,
    )
}

__all__ = ["BATCH_SPECS", "BatchSpec"]

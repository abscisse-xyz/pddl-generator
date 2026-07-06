from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest
from _sailing_helpers import generate_no_tils_problem_pddl, generate_til_problem_pddl
from simulator import (
    EventKind,
    FluentKey,
    PDDLSource,
    PredicateInstance,
    ScheduledEvent,
    SimulationState,
    SimulatorEngine,
    UnifiedPlanningParser,
)
from unified_planning.io import PDDLReader
from unified_planning.plans import ActionInstance, TimeTriggeredPlan
from unified_planning.shortcuts import OneshotPlanner, get_environment

_TRAVEL_PROBLEM_PDDL = """(define (problem travel_demo)
 (:domain travel_domain)
 (:objects
    l1 l2 l3 - location
 )
 (:init
    (is_at l1)
    (= (total_travel_time) 0)
    (is_connected l1 l2)
    (= (travel_time l1 l2) 3)
    (is_connected l2 l3)
    (= (travel_time l2 l3) 5)
 )
 (:goal (and
    (is_at l3)
 ))
 (:metric minimize (total_travel_time))
)
"""


def test_simulator_engine_executes_events_in_time_order() -> None:
    engine = SimulatorEngine(initial_state=SimulationState())

    engine.schedule(
        ScheduledEvent(
            time=Fraction(5, 1),
            priority=10,
            kind=EventKind.INTERNAL,
            description="late",
            transition=lambda state: state.set_fact(PredicateInstance("late"), True),
        )
    )
    engine.schedule(
        ScheduledEvent(
            time=Fraction(2, 1),
            priority=0,
            kind=EventKind.TIMED_EFFECT,
            description="early",
            transition=lambda state: state.set_numeric_value(FluentKey("counter"), Fraction(1, 1)),
        )
    )

    executed = engine.run_to_completion()

    assert executed == 2
    assert engine.state.time == Fraction(5, 1)
    assert engine.state.holds(PredicateInstance("late"))
    assert engine.state.numeric_value(FluentKey("counter")) == Fraction(1, 1)
    assert [entry.description for entry in engine.trace.entries] == ["early", "late"]


def test_parser_loads_temporal_sailing_problem_without_eager_grounding(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/sailing_tils/domain.pddl"),
        problem_text=generate_til_problem_pddl("til_demo", 1, [0], 1, 6),
    )

    runtime = UnifiedPlanningParser().load_runtime(source)

    assert runtime.domain.name == "sailing"
    assert runtime.problem.name == "til_demo"
    assert runtime.problem.domain_name == "sailing"
    assert len(runtime.problem.timed_effects) == 1
    assert runtime.problem.timed_effects[0].time == Fraction(12, 1)
    assert runtime.grounded_actions == ()
    assert {action.name for action in runtime.domain.actions} >= {"go_north_east", "save_person"}


def test_parser_loads_classical_travel_problem_without_eager_grounding(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/travel/domain.pddl"),
        problem_text=_TRAVEL_PROBLEM_PDDL,
    )

    runtime = UnifiedPlanningParser().load_runtime(source)

    assert runtime.domain.name == "travel_domain"
    assert runtime.grounded_actions == ()
    assert len(runtime.domain.actions) == 1
    assert runtime.domain.actions[0].name == "move"
    assert runtime.domain.actions[0].action_kind == "instantaneous"


def test_simulator_executes_classical_travel_actions_and_updates_numeric_state(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/travel/domain.pddl"),
        problem_text=_TRAVEL_PROBLEM_PDDL,
    )
    engine = SimulatorEngine.from_runtime(UnifiedPlanningParser().load_runtime(source))

    engine.start_action("move", ("l1", "l2"))
    engine.start_action("move", ("l2", "l3"))

    assert engine.goals_satisfied()
    assert engine.state.time == Fraction(0, 1)
    assert engine.state.holds(PredicateInstance("is_at", ("l3",)))
    assert engine.state.numeric_value(FluentKey("total_travel_time")) == Fraction(8, 1)


def test_simulator_apply_action_wraps_instantaneous_action_and_current_facts(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/travel/domain.pddl"),
        problem_text=_TRAVEL_PROBLEM_PDDL,
    )
    engine = SimulatorEngine.from_runtime(UnifiedPlanningParser().load_runtime(source))

    assert engine.current_facts() == (
        ("is_at", "l1"),
        ("is_connected", "l1", "l2"),
        ("is_connected", "l2", "l3"),
    )

    action = engine.apply_action("move", ("l1", "l2"))

    assert action.name == "move"
    assert action.arguments == ("l1", "l2")
    assert engine.state.time == Fraction(0, 1)
    assert engine.current_facts() == (
        ("is_at", "l2"),
        ("is_connected", "l1", "l2"),
        ("is_connected", "l2", "l3"),
    )
    assert all(fact[0] != "total_travel_time" for fact in engine.current_facts())
    assert engine.state.numeric_value(FluentKey("total_travel_time")) == Fraction(3, 1)


def test_simulator_apply_action_optionally_finishes_durative_action(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/sailing_tils/domain.pddl"),
        problem_text=generate_til_problem_pddl("til_demo", 1, [0], 1, 6),
    )
    engine = SimulatorEngine.from_runtime(UnifiedPlanningParser().load_runtime(source))

    started = engine.apply_action("go_north_east", ("b0",), finish=False)

    assert started.name == "go_north_east"
    assert started.arguments == ("b0",)
    assert engine.state.time == Fraction(0, 1)
    assert [(action.name, action.arguments) for action in engine.state.running_actions] == [
        ("go_north_east", ("b0",))
    ]
    assert engine.has_pending_events()

    engine.reset()
    finished = engine.apply_action("go_north_east", ("b0",), finish=True)

    assert finished.name == "go_north_east"
    assert engine.state.time == Fraction(1, 1)
    assert engine.state.running_actions == []
    assert any(entry.kind == EventKind.ACTION_END for entry in engine.trace.entries)


def test_simulator_handles_object_equality_and_forall_conditional_effects(tmp_path: Path) -> None:
    from unified_planning.plans import SequentialPlan

    domain_path = tmp_path / "domain.pddl"
    problem_path = tmp_path / "problem.pddl"
    domain_path.write_text(
        """(define (domain quantified-road)
  (:requirements :strips :typing :equality :conditional-effects)
  (:types car loc road)
  (:predicates
    (onroad ?c - car ?r - road)
    (at ?c - car ?l - loc)
    (marked ?l - loc)
  )
  (:action clear-road
    :parameters (?from - loc ?to - loc ?r - road)
    :precondition (and (not (= ?from ?to)) (marked ?to))
    :effect (and
      (forall (?c - car)
        (when (onroad ?c ?r)
          (and
            (not (onroad ?c ?r))
            (at ?c ?from)
          )
        )
      )
    )
  )
)""",
        encoding="utf-8",
    )
    problem_path.write_text(
        """(define (problem quantified-road-problem)
  (:domain quantified-road)
  (:objects c0 c1 - car l0 l1 - loc r0 - road)
  (:init (onroad c0 r0) (marked l1))
  (:goal (and (at c0 l0) (not (onroad c0 r0))))
)""",
        encoding="utf-8",
    )
    runtime = UnifiedPlanningParser().load_runtime(PDDLSource(domain_path=domain_path, problem_path=problem_path))
    src = runtime.source_problem
    assert src is not None
    plan = SequentialPlan(
        [
            ActionInstance(
                src.action("clear-road"),
                (src.object("l0"), src.object("l1"), src.object("r0")),
            )
        ]
    )

    engine = SimulatorEngine.from_runtime(runtime)
    engine.replay_plan(plan)

    assert engine.state.holds(PredicateInstance("at", ("c0", "l0")))
    assert not engine.state.holds(PredicateInstance("onroad", ("c0", "r0")))
    assert not engine.state.holds(PredicateInstance("at", ("c1", "l0")))


def test_simulator_executes_til_sailing_plan_and_deadline_event(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/sailing_tils/domain.pddl"),
        problem_text=generate_til_problem_pddl("til_demo", 1, [0], 1, 6),
    )

    engine = SimulatorEngine.from_runtime(UnifiedPlanningParser().load_runtime(source))

    engine.start_action("go_north_east", ("b0",))
    engine.run_until(Fraction(1, 1))
    engine.start_action("go_north_west", ("b0",))
    engine.run_until(Fraction(2, 1))
    engine.start_action("save_person", ("b0", "p0"))
    engine.run_until(Fraction(3, 1))

    assert engine.goals_satisfied()
    assert engine.state.holds(PredicateInstance("saved", ("p0",)))
    assert engine.state.numeric_value(FluentKey("x", ("b0",))) == Fraction(0, 1)
    assert engine.state.numeric_value(FluentKey("y", ("b0",))) == Fraction(6, 1)
    assert engine.state.holds(PredicateInstance("still_alive"))

    engine.run_until(Fraction(12, 1))

    assert not engine.state.holds(PredicateInstance("still_alive"))
    assert any(entry.kind == EventKind.TIMED_EFFECT for entry in engine.trace.entries)


def test_simulator_replays_time_triggered_plan(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/sailing_tils/domain.pddl"),
        problem_text=generate_til_problem_pddl("til_demo", 1, [0], 1, 6),
    )
    runtime = UnifiedPlanningParser().load_runtime(source)
    engine = SimulatorEngine.from_runtime(runtime)

    source_problem = runtime.source_problem
    assert source_problem is not None
    b0 = source_problem.object("b0")
    p0 = source_problem.object("p0")
    go_north_east = source_problem.action("go_north_east")
    go_north_west = source_problem.action("go_north_west")
    save_person = source_problem.action("save_person")

    plan = TimeTriggeredPlan(
        [
            (Fraction(0, 1), ActionInstance(go_north_east, (b0,)), Fraction(1, 1)),
            (Fraction(1, 1), ActionInstance(go_north_west, (b0,)), Fraction(1, 1)),
            (Fraction(2, 1), ActionInstance(save_person, (b0, p0)), Fraction(1, 1)),
        ]
    )

    final_state = engine.replay_plan(plan)

    assert final_state.holds(PredicateInstance("saved", ("p0",)))
    assert final_state.numeric_value(FluentKey("x", ("b0",))) == Fraction(0, 1)
    assert final_state.numeric_value(FluentKey("y", ("b0",))) == Fraction(6, 1)
    assert final_state.time == Fraction(3, 1)
    assert final_state.holds(PredicateInstance("still_alive"))

    engine.run_until(Fraction(12, 1))

    assert not final_state.holds(PredicateInstance("still_alive"))


def test_simulator_replay_plan_checks_preconditions_incrementally(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/sailing_tils/domain.pddl"),
        problem_text=generate_til_problem_pddl("til_demo", 1, [0], 1, 6),
    )
    runtime = UnifiedPlanningParser().load_runtime(source)
    engine = SimulatorEngine.from_runtime(runtime)

    source_problem = runtime.source_problem
    assert source_problem is not None
    b0 = source_problem.object("b0")
    p0 = source_problem.object("p0")
    save_person = source_problem.action("save_person")

    invalid_plan = TimeTriggeredPlan(
        [
            (Fraction(0, 1), ActionInstance(save_person, (b0, p0)), Fraction(1, 1)),
        ]
    )

    with pytest.raises(ValueError, match="not applicable"):
        engine.replay_plan(invalid_plan)

    assert engine.state.time == Fraction(0, 1)
    assert not engine.state.holds(PredicateInstance("saved", ("p0",)))


def test_simulator_executes_no_tils_sailing_plan_with_overall_controller(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/sailing_no_tils/domain.pddl"),
        problem_text=generate_no_tils_problem_pddl("no_tils_demo", 1, [0], 1, 6),
    )

    engine = SimulatorEngine.from_runtime(UnifiedPlanningParser().load_runtime(source))

    assert {action.name for action in engine.applicable_actions()} == {"overall"}

    engine.start_action("overall")
    assert engine.state.holds(PredicateInstance("started"))

    engine.start_action("go_north_east", ("b0",))
    engine.run_until(Fraction(1, 1))
    engine.start_action("go_north_west", ("b0",))
    engine.run_until(Fraction(2, 1))
    engine.start_action("save_person", ("b0", "p0"))
    engine.run_until(Fraction(3, 1))

    assert engine.goals_satisfied()
    assert engine.state.holds(PredicateInstance("still_alive"))

    engine.run_until(Fraction(12, 1))

    assert not engine.state.holds(PredicateInstance("still_alive"))
    assert any("overall" in entry.description for entry in engine.trace.entries)


def test_simulator_rejects_non_applicable_save_action(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/sailing_tils/domain.pddl"),
        problem_text=generate_til_problem_pddl("til_demo", 1, [0], 1, 6),
    )
    engine = SimulatorEngine.from_runtime(UnifiedPlanningParser().load_runtime(source))

    with pytest.raises(ValueError, match="not applicable"):
        engine.start_action("save_person", ("b0", "p0"))


def test_simulator_rejects_action_when_resource_is_busy(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/sailing_tils/domain.pddl"),
        problem_text=generate_til_problem_pddl("til_demo", 1, [0], 1, 6),
    )
    engine = SimulatorEngine.from_runtime(UnifiedPlanningParser().load_runtime(source))

    engine.start_action("go_north_east", ("b0",))

    with pytest.raises(ValueError, match="not applicable"):
        engine.start_action("go_est", ("b0",))


def test_simulator_requires_overall_before_no_tils_actions(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/sailing_no_tils/domain.pddl"),
        problem_text=generate_no_tils_problem_pddl("no_tils_demo", 1, [0], 1, 6),
    )
    engine = SimulatorEngine.from_runtime(UnifiedPlanningParser().load_runtime(source))

    with pytest.raises(ValueError, match="not applicable"):
        engine.start_action("go_north_east", ("b0",))


def test_simulator_rejects_unknown_action_name(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/sailing_tils/domain.pddl"),
        problem_text=generate_til_problem_pddl("til_demo", 1, [0], 1, 6),
    )
    engine = SimulatorEngine.from_runtime(UnifiedPlanningParser().load_runtime(source))

    with pytest.raises(KeyError, match="Unknown grounded action"):
        engine.start_action("teleport", ("b0",))


def test_simulator_rejects_scheduling_events_in_the_past() -> None:
    engine = SimulatorEngine(initial_state=SimulationState(time=Fraction(3, 1)))

    with pytest.raises(ValueError, match="in the past"):
        engine.schedule(
            ScheduledEvent(
                time=Fraction(2, 1),
                priority=0,
                kind=EventKind.INTERNAL,
                description="past",
                transition=lambda state: None,
            )
        )


def test_simulator_run_to_completion_honors_max_steps() -> None:
    engine = SimulatorEngine(initial_state=SimulationState())
    for index in range(2):
        engine.schedule(
            ScheduledEvent(
                time=Fraction(index + 1, 1),
                priority=0,
                kind=EventKind.INTERNAL,
                description=f"event-{index}",
                transition=lambda state: None,
            )
        )

    with pytest.raises(RuntimeError, match="Maximum number of simulator steps reached"):
        engine.run_to_completion(max_steps=1)


def test_simulator_reset_restores_initial_state_and_reschedules_timed_effects(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/sailing_tils/domain.pddl"),
        problem_text=generate_til_problem_pddl("til_demo", 1, [0], 1, 6),
    )
    engine = SimulatorEngine.from_runtime(UnifiedPlanningParser().load_runtime(source))

    engine.start_action("go_north_east", ("b0",))
    engine.run_until(Fraction(12, 1))
    assert not engine.state.holds(PredicateInstance("still_alive"))

    engine.reset()

    assert engine.state.time == Fraction(0, 1)
    assert engine.state.holds(PredicateInstance("still_alive"))
    assert engine.has_pending_events()
    assert len(engine.trace.entries) == 0


def test_simulator_replays_default_up_planner_plan_when_available(tmp_path: Path) -> None:
    get_environment().credits_stream = None
    domain_path = tmp_path / "domain.pddl"
    problem_path = tmp_path / "problem.pddl"
    domain_path.write_text(
        """(define (domain simple-temporal)
  (:requirements :typing :durative-actions)
  (:types loc)
  (:predicates (at ?l - loc) (connected ?from - loc ?to - loc))
  (:durative-action move
    :parameters (?from - loc ?to - loc)
    :duration (= ?duration 1)
    :condition (and (at start (at ?from)) (at start (connected ?from ?to)))
    :effect (and (at start (not (at ?from))) (at end (at ?to)))
  )
)""",
        encoding="utf-8",
    )
    problem_path.write_text(
        """(define (problem simple-problem)
  (:domain simple-temporal)
  (:objects a b - loc)
  (:init (at a) (connected a b))
  (:goal (at b))
  (:metric minimize (total-time))
)""",
        encoding="utf-8",
    )

    problem = PDDLReader().parse_problem(str(domain_path), str(problem_path))
    try:
        with OneshotPlanner(problem_kind=problem.kind) as planner:
            result = planner.solve(problem)
    except PermissionError as error:
        pytest.skip(f"Default UP planner is unavailable in this environment: {error}")
    except Exception as error:
        if "Operation not permitted" in str(error):
            pytest.skip(f"Default UP planner is unavailable in this environment: {error}")
        raise

    assert result.plan is not None

    engine = SimulatorEngine.from_pddl(domain_path, problem_path)
    final_state = engine.replay_plan(result.plan)

    assert final_state.time == Fraction(1, 1)
    assert final_state.holds(PredicateInstance("at", ("b",)))


def test_simulator_replays_sequential_plan(tmp_path: Path) -> None:
    """Sequential branch in replay_plan was previously uncovered by real-plan tests."""
    from unified_planning.plans import SequentialPlan

    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/sailing_tils/domain.pddl"),
        problem_text=generate_til_problem_pddl("til_demo", 1, [0], 1, 6),
    )
    runtime = UnifiedPlanningParser().load_runtime(source)
    engine = SimulatorEngine.from_runtime(runtime)
    src = runtime.source_problem
    assert src is not None
    b0 = src.object("b0")
    p0 = src.object("p0")

    plan = SequentialPlan(
        [
            ActionInstance(src.action("go_north_east"), (b0,)),
            ActionInstance(src.action("go_north_west"), (b0,)),
            ActionInstance(src.action("save_person"), (b0, p0)),
        ]
    )

    final_state = engine.replay_plan(plan)
    assert final_state.holds(PredicateInstance("saved", ("p0",)))
    assert final_state.time == Fraction(3, 1)


def test_simulator_replay_unwraps_hierarchical_plan(tmp_path: Path) -> None:
    """A HierarchicalPlan-shaped object should recurse onto its `action_plan`."""
    from unified_planning.plans import SequentialPlan

    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/sailing_tils/domain.pddl"),
        problem_text=generate_til_problem_pddl("til_demo", 1, [0], 1, 6),
    )
    runtime = UnifiedPlanningParser().load_runtime(source)
    engine = SimulatorEngine.from_runtime(runtime)
    src = runtime.source_problem
    assert src is not None
    b0 = src.object("b0")
    p0 = src.object("p0")

    flat = SequentialPlan(
        [
            ActionInstance(src.action("go_north_east"), (b0,)),
            ActionInstance(src.action("go_north_west"), (b0,)),
            ActionInstance(src.action("save_person"), (b0, p0)),
        ]
    )

    # Engine dispatch keys on `type(plan).__name__`, so any class named
    # `HierarchicalPlan` with an `action_plan` attribute exercises the unwrap.
    class HierarchicalPlan:  # noqa: D401 — test stand-in for unified_planning's class
        def __init__(self, action_plan):
            self.action_plan = action_plan

    final_state = engine.replay_plan(HierarchicalPlan(flat))
    assert final_state.holds(PredicateInstance("saved", ("p0",)))
    assert final_state.time == Fraction(3, 1)


def test_simulator_replay_rejects_unsupported_plan_with_clear_error() -> None:
    engine = SimulatorEngine()

    class PartialOrderPlan:  # mimics unified_planning's class for type-name dispatch
        pass

    with pytest.raises(NotImplementedError, match="PartialOrderPlan"):
        engine.replay_plan(PartialOrderPlan())


def _write_problem_instance(tmp_path: Path, domain_path: Path, problem_text: str) -> PDDLSource:
    problem_path = tmp_path / "problem.pddl"
    problem_path.write_text(problem_text, encoding="utf-8")
    return PDDLSource(domain_path=domain_path, problem_path=problem_path)

"""Serialization helpers for simulator persistence backends."""

from __future__ import annotations

import json
from fractions import Fraction

from ..events import EventKind, ScheduledEvent
from ..state import FluentKey, PredicateInstance, RunningAction, SimulationState


def fraction_to_text(value: Fraction) -> str:
    """Serialize a rational value without losing precision."""

    return f"{value.numerator}/{value.denominator}"


def fraction_from_text(value: str) -> Fraction:
    """Deserialize a rational value produced by :func:`fraction_to_text`."""

    numerator, denominator = value.split("/", maxsplit=1)
    return Fraction(int(numerator), int(denominator))


def serialize_state(state: SimulationState) -> tuple[str, str, str]:
    """Serialize a simulation state into JSON payloads."""

    facts = [
        {"name": fact.name, "arguments": list(fact.arguments)}
        for fact in sorted(state.facts, key=lambda item: (item.name, item.arguments))
    ]
    numeric_values = [
        {
            "name": key.name,
            "arguments": list(key.arguments),
            "value": fraction_to_text(value),
        }
        for key, value in sorted(state.numeric_values.items(), key=lambda item: (item[0].name, item[0].arguments))
    ]
    running_actions = [
        {
            "name": action.name,
            "arguments": list(action.arguments),
            "started_at": fraction_to_text(action.started_at),
            "ends_at": fraction_to_text(action.ends_at),
        }
        for action in sorted(state.running_actions, key=lambda item: (item.started_at, item.name, item.arguments))
    ]
    return json.dumps(facts), json.dumps(numeric_values), json.dumps(running_actions)


def deserialize_state(
    *,
    sim_time: Fraction,
    facts_json: str,
    numeric_values_json: str,
    running_actions_json: str,
) -> SimulationState:
    """Deserialize a simulation state from JSON payloads."""

    facts = {
        PredicateInstance(name=item["name"], arguments=tuple(item["arguments"])) for item in json.loads(facts_json)
    }
    numeric_values = {
        FluentKey(name=item["name"], arguments=tuple(item["arguments"])): fraction_from_text(item["value"])
        for item in json.loads(numeric_values_json)
    }
    running_actions = [
        RunningAction(
            name=item["name"],
            arguments=tuple(item["arguments"]),
            started_at=fraction_from_text(item["started_at"]),
            ends_at=fraction_from_text(item["ends_at"]),
        )
        for item in json.loads(running_actions_json)
    ]
    return SimulationState(
        time=sim_time,
        facts=facts,
        numeric_values=numeric_values,
        running_actions=running_actions,
    )


def serialize_pending_events(events: tuple[ScheduledEvent, ...]) -> str:
    """Serialize pending events as metadata for inspection and resume planning."""

    serializable_events = [
        {
            "time": fraction_to_text(event.time),
            "priority": event.priority,
            "kind": event.kind.value,
            "description": event.description,
        }
        for event in sorted(events, key=lambda item: (item.time, item.priority, item.kind.value, item.description))
    ]
    return json.dumps(serializable_events)


def deserialize_pending_events(events_json: str) -> tuple[ScheduledEvent, ...]:
    """Deserialize pending event metadata.

    The original transition callbacks are not persisted yet, so deserialized
    events are inspection-only placeholders.
    """

    pending_events: list[ScheduledEvent] = []
    for item in json.loads(events_json):
        pending_events.append(
            ScheduledEvent(
                time=fraction_from_text(item["time"]),
                priority=int(item["priority"]),
                kind=EventKind(item["kind"]),
                description=item["description"],
                transition=lambda state: None,
            )
        )
    return tuple(pending_events)

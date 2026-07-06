# Plan Topologies

This file is a compact reference for available plan topologies and the
corresponding modeling style they assume.

Covered here:

- `SequentialPlan`
- `TimeTriggeredPlan`
- `HierarchicalPlan`
- agent-scoped `SequentialPlan` in multi-agent problems

Related plan families not covered here:

- `PartialOrderPlan`
- `STNPlan`
- `ContingentPlan`
- scheduling-specific plan objects

The sections below are ordered from simplest to most complex.

## 1. SequentialPlan

Idea:

- a totally ordered list of actions
- one action starts after the previous one ends

### unified-planning snippet

```python
from unified_planning.shortcuts import *
import unified_planning as up

Location = UserType("Location")
l1 = Object("l1", Location)
l2 = Object("l2", Location)

move = InstantaneousAction("move", l_from=Location, l_to=Location)

plan = up.plans.SequentialPlan(
    [
        up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2))),
    ]
)
```

### Simple PDDL domain

```lisp
(define (domain seq_move_domain)
 (:requirements :strips :typing)
 (:types location)
 (:predicates
   (is_at ?l - location)
   (connected ?from - location ?to - location)
 )
 (:action move
  :parameters (?from - location ?to - location)
  :precondition (and
    (is_at ?from)
    (connected ?from ?to)
  )
  :effect (and
    (not (is_at ?from))
    (is_at ?to)
  )
 )
)
```

### Simple PDDL problem

```lisp
(define (problem seq_move_problem)
 (:domain seq_move_domain)
 (:objects l1 l2 - location)
 (:init
   (is_at l1)
   (connected l1 l2)
 )
 (:goal (and
   (is_at l2)
 ))
)
```

## 2. Agent-Scoped SequentialPlan

Idea:

- still a total order
- each action instance also carries the owning agent
- same topology as a sequential plan, but with explicit execution ownership

### unified-planning snippet

```python
from unified_planning.shortcuts import *
import unified_planning as up

problem = MultiAgentProblem("ma_basic")
Location = UserType("Location")

robot = Agent("robot", problem)
move = InstantaneousAction("move", l_from=Location, l_to=Location)

l1 = Object("l1", Location)
l2 = Object("l2", Location)

plan = up.plans.SequentialPlan(
    [
        up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)), robot),
    ]
)
```

### Simple MA-PDDL domain

```lisp
(define (domain ma_seq_move_domain)
 (:requirements :multi-agent :factored-privacy :typing)
 (:types location ag - object
    robot_type - ag
 )
 (:predicates
   (connected ?from - location ?to - location)
   (:private
    (at ?agent - ag ?l - location)
   )
 )
 (:action move
  :parameters (?robot - robot_type ?from - location ?to - location)
  :precondition (and
    (at ?robot ?from)
    (connected ?from ?to)
  )
  :effect (and
    (not (at ?robot ?from))
    (at ?robot ?to)
  )
 )
)
```

### Simple MA-PDDL problem

```lisp
(define (problem ma_seq_move_problem)
 (:domain ma_seq_move_domain)
 (:objects
   l1 l2 - location
   robot - robot_type
 )
 (:init
   (connected l1 l2)
   (at robot l1)
 )
 (:goal (and
   (at robot l2)
 ))
)
```

## 3. TimeTriggeredPlan

Idea:

- each action has an explicit start time
- actions may overlap
- optional duration can be attached directly in the plan

### unified-planning snippet

```python
from fractions import Fraction
from unified_planning.shortcuts import *
import unified_planning as up

Location = UserType("Location")
l1 = Object("l1", Location)
l2 = Object("l2", Location)

move = DurativeAction("move", l_from=Location, l_to=Location)

plan = up.plans.TimeTriggeredPlan(
    [
        (
            Fraction(0, 1),
            up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2))),
            Fraction(1, 1),
        ),
    ]
)
```

### Simple PDDL domain

```lisp
(define (domain temporal_move_domain)
 (:requirements :strips :typing :durative-actions)
 (:types location)
 (:predicates
   (is_at ?l - location)
   (connected ?from - location ?to - location)
 )
 (:durative-action move
  :parameters (?from - location ?to - location)
  :duration (= ?duration 1)
  :condition (and
    (at start (is_at ?from))
    (over all (connected ?from ?to))
  )
  :effect (and
    (at end (not (is_at ?from)))
    (at end (is_at ?to))
  )
 )
)
```

### Simple PDDL problem

```lisp
(define (problem temporal_move_problem)
 (:domain temporal_move_domain)
 (:objects l1 l2 - location)
 (:init
   (is_at l1)
   (connected l1 l2)
 )
 (:goal (and
   (is_at l2)
 ))
)
```

## 4. HierarchicalPlan over a SequentialPlan

Idea:

- the executable part is a flat plan
- on top of it, a decomposition explains how high-level tasks were refined
- this is more than ordering: it records abstraction structure

### unified-planning snippet

```python
from unified_planning.shortcuts import *
import unified_planning as up
from unified_planning.plans.hierarchical_plan import (
    Decomposition,
    HierarchicalPlan,
    MethodInstance,
)

Location = UserType("Location")
l1 = Object("l1", Location)
l2 = Object("l2", Location)

move = InstantaneousAction("move", l_from=Location, l_to=Location)
flat_plan = up.plans.SequentialPlan(
    [
        up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2))),
    ]
)

# Example shape only: one root task decomposed by one method into one move step.
go_direct = Method("go_direct", target=Location)
t_go = type("TaskRef", (), {"identifier": "t_go"})()
t_move = type("TaskRef", (), {"identifier": "t_move"})()

plan = HierarchicalPlan(
    flat_plan,
    Decomposition(
        {
            t_go.identifier: MethodInstance(
                go_direct,
                parameters=(l2,),
                decomposition=Decomposition(
                    {
                        t_move.identifier: flat_plan.actions[0],
                    }
                ),
            )
        }
    ),
)
```

### Simple HDDL domain

```lisp
(define (domain htn_move_domain)
 (:requirements :strips :typing :hierarchy)
 (:types location)
 (:predicates
   (is_at ?l - location)
   (connected ?from - location ?to - location)
 )
 (:task go
  :parameters (?target - location)
 )
 (:method go_direct
  :parameters (?from - location ?target - location)
  :task (go ?target)
  :precondition (and
    (is_at ?from)
    (connected ?from ?target)
  )
  :subtasks (and
    (t_move (move ?from ?target))
  )
 )
 (:action move
  :parameters (?from - location ?to - location)
  :precondition (and
    (is_at ?from)
    (connected ?from ?to)
  )
  :effect (and
    (not (is_at ?from))
    (is_at ?to)
  )
 )
)
```

### Simple HDDL problem

```lisp
(define (problem htn_move_problem)
 (:domain htn_move_domain)
 (:objects l1 l2 - location)
 (:init
   (is_at l1)
   (connected l1 l2)
 )
 (:htn
  :tasks (and
    (t1 (go l2))
  )
 )
)
```

## 5. HierarchicalPlan over a TimeTriggeredPlan

Idea:

- combines explicit temporal scheduling with hierarchical decomposition
- this is the richest plan shape used in the example package

### unified-planning snippet

```python
from fractions import Fraction
from unified_planning.shortcuts import *
import unified_planning as up
from unified_planning.plans.hierarchical_plan import (
    Decomposition,
    HierarchicalPlan,
    MethodInstance,
)

Location = UserType("Location")
l1 = Object("l1", Location)
l2 = Object("l2", Location)

move = DurativeAction("move", l_from=Location, l_to=Location)
flat_plan = up.plans.TimeTriggeredPlan(
    [
        (
            Fraction(0, 1),
            up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2))),
            Fraction(1, 1),
        ),
    ]
)

go_direct_t = Method("go_direct_t", target=Location)
t_go = type("TaskRef", (), {"identifier": "t_go"})()
t_move = type("TaskRef", (), {"identifier": "t_move"})()

plan = HierarchicalPlan(
    flat_plan,
    Decomposition(
        {
            t_go.identifier: MethodInstance(
                go_direct_t,
                parameters=(l2,),
                decomposition=Decomposition(
                    {
                        t_move.identifier: flat_plan.timed_actions[0][1],
                    }
                ),
            )
        }
    ),
)
```

### Simple HDDL-style temporal domain

```lisp
(define (domain htn_temporal_move_domain)
 (:requirements :strips :typing :durative-actions :hierarchy)
 (:types location)
 (:predicates
   (is_at ?l - location)
   (connected ?from - location ?to - location)
 )
 (:task go
  :parameters (?target - location)
 )
 (:method go_direct_t
  :parameters (?from - location ?target - location)
  :task (go ?target)
  :precondition (and
    (is_at ?from)
    (connected ?from ?target)
  )
  :ordered-subtasks (and
    (t_move (move ?from ?target))
  )
 )
 (:durative-action move
  :parameters (?from - location ?to - location)
  :duration (= ?duration 1)
  :condition (and
    (at start (is_at ?from))
    (over all (connected ?from ?to))
  )
  :effect (and
    (at end (not (is_at ?from)))
    (at end (is_at ?to))
  )
 )
)
```

### Simple HDDL-style temporal problem

```lisp
(define (problem htn_temporal_move_problem)
 (:domain htn_temporal_move_domain)
 (:objects l1 l2 - location)
 (:init
   (is_at l1)
   (connected l1 l2)
 )
 (:htn
  :tasks (and
    (t1 (go l2))
  )
 )
)
```

## Notes

- Motion-planning constraints, numeric fluents, typing complexity, and
  multi-agent ownership do not automatically introduce a new plan topology.
- The main structural jump is usually from total order, to explicit timing,
  to hierarchical decomposition layered over an executable flat plan.

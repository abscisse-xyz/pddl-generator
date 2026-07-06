# Example Problem Reference

This file documents PDDL example problems. For each problem, it includes a short explanation, a problem definition using unified-planning API and the correspond PDDL domain.

## Contents

- [minimals](#minimals)
- [variants](#variants)
- [processes](#processes)
- [multi_agent](#multi_agent)
- [hierarchical](#hierarchical)
- [realistic](#realistic)
- [tamp](#tamp)

## minimals

### Problems

- [basic](#basic)
- [basic_conditional](#basic_conditional)
- [basic_oversubscription](#basic_oversubscription)
- [basic_tils](#basic_tils)
- [complex_conditional](#complex_conditional)
- [basic_without_negative_preconditions](#basic_without_negative_preconditions)
- [basic_nested_conjunctions](#basic_nested_conjunctions)
- [basic_exists](#basic_exists)
- [basic_forall](#basic_forall)
- [temporal_conditional](#temporal_conditional)
- [basic_with_costs](#basic_with_costs)
- [basic_with_default_values](#basic_with_default_values)
- [counter](#counter)
- [counter_to_50](#counter_to_50)
- [temporal_counter](#temporal_counter)
- [basic_with_object_constant](#basic_with_object_constant)
- [basic_numeric](#basic_numeric)
- [basic_numeric_with_timed_effect](#basic_numeric_with_timed_effect)
- [basic_undef_bool](#basic_undef_bool)
- [basic_undef_numeric](#basic_undef_numeric)
- [undef_numeric_with_timed_effects](#undef_numeric_with_timed_effects)
- [durative_continuous_example](#durative_continuous_example)

### basic

This example defines `basic` with 1 fluent(s), 1 action(s), and 0 object(s). Primary action(s): a. Goal summary: x. Special features: classical planning only.

#### unified-planning

```python
    # basic
    x = Fluent("x")
    a = InstantaneousAction("a")
    a.add_precondition(Not(x))
    a.add_effect(x, True)
    problem = Problem("basic")
    problem.add_fluent(x)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.add_goal(x)
```

#### PDDL domain

```lisp
(define (domain basic_domain)
 (:requirements :strips :negative-preconditions)
 (:predicates 
             (x)
 )
 (:action a
  :parameters ()
  :precondition (and (not (x)))
  :effect (and (x)))
)
```

### basic_conditional

This example defines `basic_conditional` with 2 fluent(s), 2 action(s), and 0 object(s). Primary action(s): a_x, a_y. Goal summary: x. Special features: conditional effects.

#### unified-planning

```python
    # basic conditional
    x = Fluent("x")
    y = Fluent("y")
    a_x = InstantaneousAction("a_x")
    a_y = InstantaneousAction("a_y")
    a_x.add_precondition(Not(x))
    a_x.add_effect(x, True, y)
    a_y.add_precondition(Not(y))
    a_y.add_effect(y, True)
    problem = Problem("basic_conditional")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(a_x)
    problem.add_action(a_y)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y, False)
    problem.add_goal(x)
```

#### PDDL domain

```lisp
(define (domain basic_conditional_domain)
 (:requirements :strips :negative-preconditions :conditional-effects)
 (:predicates 
             (x)
             (y)
 )
 (:action a_x
  :parameters ()
  :precondition (and (not (x)))
  :effect (and (when (y) (x))))
 (:action a_y
  :parameters ()
  :precondition (and (not (y)))
  :effect (and (y)))
)
```

### basic_oversubscription

This example defines `basic_oversubscription` with 1 fluent(s), 1 action(s), and 0 object(s). Primary action(s): a. Goal summary: No explicit top-level goal is declared.. Special features: 1 quality metric(s).

#### unified-planning

```python
    # basic oversubscription
    x = Fluent("x")
    a = InstantaneousAction("a")
    a.add_precondition(Not(x))
    a.add_effect(x, True)
    problem = Problem("basic_oversubscription")
    problem.add_fluent(x)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    qm = up.model.metrics.Oversubscription({FluentExp(x): 10})
    problem.add_quality_metric(qm)
```

#### PDDL domain

```lisp
(define (domain basic_oversubscription_domain)
 (:requirements :strips :negative-preconditions)
 (:predicates 
             (x)
 )
 (:action a
  :parameters ()
  :precondition (and (not (x)))
  :effect (and (x)))
)
```

### basic_tils

This example defines `basic_tils` with 2 fluent(s), 1 action(s), and 0 object(s). Primary action(s): a. Goal summary: x. Special features: continuous time, timed effects.

#### unified-planning

```python
    # basic tils (timed initial literals)
    x = Fluent("x")
    y = Fluent("y")
    da = DurativeAction("a")
    da.set_fixed_duration(1)
    da.add_effect(EndTiming(), x, True)
    da.add_condition(TimeInterval(StartTiming(), EndTiming()), y)
    problem = Problem("basic_tils")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(da)
    problem.set_initial_value(x, False)
    problem.add_timed_effect(GlobalStartTiming(5), x, False)
    problem.set_initial_value(y, False)
    problem.add_timed_effect(GlobalStartTiming(2), y, True)
    problem.add_timed_effect(GlobalStartTiming(8), y, False)
    problem.add_goal(x)
```

#### PDDL domain

```lisp
(define (domain basic_tils_domain)
 (:requirements :strips :durative-actions :timed-initial-literals)
 (:predicates 
             (x)
             (y)
 )
 (:durative-action a
  :parameters ()
  :duration (= ?duration 1)
  :condition (and 
                 (at start (y))(over all (y))(at end (y))
             )
  :effect (and
              (at end (x))
          )
 )
)
```

### complex_conditional

This example defines `complex_conditional` with 8 fluent(s), 4 action(s), and 0 object(s). Primary action(s): act, act_0, act_1, act_2. Goal summary: fluent_a; fluent_b; .... Special features: conditional effects.

#### unified-planning

```python
    # complex conditional
    fluent_a = Fluent("fluent_a")
    fluent_b = Fluent("fluent_b")
    fluent_c = Fluent("fluent_c")
    fluent_d = Fluent("fluent_d")
    fluent_k = Fluent("fluent_k")
    fluent_x = Fluent("fluent_x")
    fluent_y = Fluent("fluent_y")
    fluent_z = Fluent("fluent_z")
    a_act = InstantaneousAction("act")
    a_0_act = InstantaneousAction("act_0")
    a_1_act = InstantaneousAction("act_1")
    a_2_act = InstantaneousAction("act_2")
    a_act.add_precondition(Not(fluent_a))
    a_act.add_effect(fluent_a, TRUE())
    a_act.add_effect(fluent_k, TRUE(), fluent_b)
    a_act.add_effect(fluent_x, TRUE(), Not(fluent_c))
    a_act.add_effect(fluent_y, FALSE(), fluent_d)
    a_0_act.add_precondition(Not(fluent_a))
    a_0_act.add_precondition(fluent_d)
    a_0_act.add_effect(fluent_b, TRUE())
    a_1_act.add_precondition(Not(fluent_a))
    a_1_act.add_precondition(fluent_d)
    a_1_act.add_precondition(fluent_b)
    a_1_act.add_effect(fluent_c, FALSE(), fluent_c)
    a_1_act.add_effect(fluent_c, TRUE(), Not(fluent_c))
    a_2_act.add_effect(fluent_a, FALSE())
    a_2_act.add_effect(fluent_d, TRUE())
    a_2_act.add_effect(fluent_z, FALSE(), fluent_z)
    a_2_act.add_effect(fluent_z, TRUE(), Not(fluent_z))
    problem = Problem("complex_conditional")
    problem.add_fluent(fluent_a)
    problem.add_fluent(fluent_b)
    problem.add_fluent(fluent_c)
    problem.add_fluent(fluent_d)
    problem.add_fluent(fluent_k)
    problem.add_fluent(fluent_x)
    problem.add_fluent(fluent_y)
    problem.add_fluent(fluent_z)
    problem.add_action(a_act)
    problem.add_action(a_0_act)
    problem.add_action(a_1_act)
    problem.add_action(a_2_act)
    problem.set_initial_value(fluent_a, True)
    problem.set_initial_value(fluent_b, False)
    problem.set_initial_value(fluent_c, True)
    problem.set_initial_value(fluent_d, False)
    problem.set_initial_value(fluent_k, False)
    problem.set_initial_value(fluent_x, False)
    problem.set_initial_value(fluent_y, True)
    problem.set_initial_value(fluent_z, False)
    problem.add_goal(fluent_a)
    problem.add_goal(fluent_b)
    problem.add_goal(Not(fluent_c))
    problem.add_goal(fluent_d)
    problem.add_goal(fluent_k)
    problem.add_goal(fluent_x)
    problem.add_goal(Not(fluent_y))
    problem.add_goal(fluent_z)
```

#### PDDL domain

```lisp
(define (domain complex_conditional_domain)
 (:requirements :strips :negative-preconditions :conditional-effects)
 (:predicates 
             (fluent_a)
             (fluent_b)
             (fluent_c)
             (fluent_d)
             (fluent_k)
             (fluent_x)
             (fluent_y)
             (fluent_z)
 )
 (:action act
  :parameters ()
  :precondition (and (not (fluent_a)))
  :effect (and (fluent_a) (when (fluent_b) (fluent_k)) (when (not (fluent_c)) (fluent_x)) (when (fluent_d) (not (fluent_y)))))
 (:action act_0
  :parameters ()
  :precondition (and (not (fluent_a)) (fluent_d))
  :effect (and (fluent_b)))
 (:action act_1
  :parameters ()
  :precondition (and (not (fluent_a)) (fluent_d) (fluent_b))
  :effect (and (when (fluent_c) (not (fluent_c))) (when (not (fluent_c)) (fluent_c))))
 (:action act_2
  :parameters ()
  :effect (and (not (fluent_a)) (fluent_d) (when (fluent_z) (not (fluent_z))) (when (not (fluent_z)) (fluent_z))))
)
```

### basic_without_negative_preconditions

This example defines `basic_without_negative_preconditions` with 2 fluent(s), 1 action(s), and 0 object(s). Primary action(s): a. Goal summary: x. Special features: classical planning only.

#### unified-planning

```python
    # basic without negative preconditions
    x = Fluent("x")
    y = Fluent("y")
    a = InstantaneousAction("a")
    a.add_precondition(y)
    a.add_effect(x, True)
    problem = Problem("basic_without_negative_preconditions")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y, True)
    problem.add_goal(x)
```

#### PDDL domain

```lisp
(define (domain basic_without_negative_preconditions_domain)
 (:requirements :strips)
 (:predicates 
             (x)
             (y)
 )
 (:action a
  :parameters ()
  :precondition (and (y))
  :effect (and (x)))
)
```

### basic_nested_conjunctions

This example defines `basic_nested_conjunctions` with 5 fluent(s), 1 action(s), and 0 object(s). Primary action(s): a. Goal summary: (x and (y and z and (j and k))). Special features: classical planning only.

#### unified-planning

```python
    # basic nested conjunctions
    problem = Problem("basic_nested_conjunctions")
    x = problem.add_fluent("x")
    y = problem.add_fluent("y")
    z = problem.add_fluent("z")
    j = problem.add_fluent("j")
    k = problem.add_fluent("k")

    a = InstantaneousAction("a")
    a.add_precondition(And(y, And(z, j, k)))
    a.add_effect(x, True)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y, True)
    problem.set_initial_value(z, True)
    problem.set_initial_value(j, True)
    problem.set_initial_value(k, True)
    problem.add_goal(And(x, And(y, z, And(j, k))))
```

#### PDDL domain

```lisp
(define (domain basic_nested_conjunctions_domain)
 (:requirements :strips)
 (:predicates 
             (x)
             (y)
             (z)
             (j)
             (k)
 )
 (:action a
  :parameters ()
  :precondition (and (y) (z) (j) (k))
  :effect (and (x)))
)
```

### basic_exists

This example defines `basic_exists` with 2 fluent(s), 1 action(s), and 2 object(s). Primary action(s): a. Goal summary: x. Special features: existential conditions.

#### unified-planning

```python
    # basic exists
    sem = UserType("Semaphore")
    x = Fluent("x")
    y = Fluent("y", BoolType(), semaphore=sem)
    o1 = Object("o1", sem)
    o2 = Object("o2", sem)
    s_var = Variable("s", sem)
    a = InstantaneousAction("a")
    a.add_precondition(Exists(FluentExp(y, [s_var]), s_var))
    a.add_effect(x, True)
    problem = Problem("basic_exists")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_object(o1)
    problem.add_object(o2)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y(o1), True)
    problem.set_initial_value(y(o2), False)
    problem.add_goal(x)
```

#### PDDL domain

```lisp
(define (domain basic_exists_domain)
 (:requirements :strips :typing :existential-preconditions)
 (:types semaphore)
 (:predicates 
             (x)
             (y ?semaphore - semaphore)
 )
 (:action a
  :parameters ()
  :precondition (and (exists (?s - semaphore)
 (y ?s)))
  :effect (and (x)))
)
```

### basic_forall

This example defines `basic_forall` with 2 fluent(s), 1 action(s), and 2 object(s). Primary action(s): a. Goal summary: x. Special features: universal conditions.

#### unified-planning

```python
    # basic forall
    sem = UserType("Semaphore")
    x = Fluent("x")
    y = Fluent("y", BoolType(), semaphore=sem)
    s_var = Variable("s", sem)
    a = InstantaneousAction("a")
    a.add_precondition(Forall(Not(y(s_var)), s_var))
    a.add_effect(x, True)
    problem = Problem("basic_forall")
    problem.add_fluent(x)
    problem.add_fluent(y)
    o1 = problem.add_object("o1", sem)
    o2 = problem.add_object("o2", sem)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y(o1), False)
    problem.set_initial_value(y(o2), False)
    problem.add_goal(x)
```

#### PDDL domain

```lisp
(define (domain basic_forall_domain)
 (:requirements :strips :typing :negative-preconditions :universal-preconditions)
 (:types semaphore)
 (:predicates 
             (x)
             (y ?semaphore - semaphore)
 )
 (:action a
  :parameters ()
  :precondition (and (forall (?s - semaphore)
 (not (y ?s))))
  :effect (and (x)))
)
```

### temporal_conditional

This example defines `temporal_conditional` with 4 fluent(s), 2 action(s), and 2 object(s). Primary action(s): set_giver, take_ok. Goal summary: is_ok(o1). Special features: continuous time, conditional effects.

#### unified-planning

```python
    # temporal conditional
    Obj = UserType("Obj")
    is_same_obj = Fluent("is_same_obj", BoolType(), object_1=Obj, object_2=Obj)
    is_ok = Fluent("is_ok", BoolType(), test=Obj)
    is_ok_giver = Fluent("is_ok_giver", BoolType(), test=Obj)
    ok_given = Fluent("ok_given")
    set_giver = DurativeAction("set_giver", param_y=Obj)
    param_y = set_giver.parameter("param_y")
    set_giver.set_fixed_duration(2)
    set_giver.add_condition(StartTiming(), Not(is_ok_giver(param_y)))
    set_giver.add_effect(StartTiming(), is_ok_giver(param_y), True)
    set_giver.add_effect(EndTiming(), is_ok_giver(param_y), False)
    take_ok = DurativeAction("take_ok", param_x=Obj, param_y=Obj)
    param_x = take_ok.parameter("param_x")
    param_y = take_ok.parameter("param_y")
    take_ok.set_fixed_duration(3)
    take_ok.add_condition(StartTiming(), Not(is_ok(param_x)))
    take_ok.add_condition(StartTiming(), Not(is_ok_giver(param_y)))
    take_ok.add_condition(StartTiming(), Not(FluentExp(is_same_obj, [param_x, param_y])))
    take_ok.add_effect(EndTiming(), is_ok(param_x), True, is_ok_giver(param_y))
    take_ok.add_effect(EndTiming(), ok_given, True)
    o1 = Object("o1", Obj)
    o2 = Object("o2", Obj)
    problem = Problem("temporal_conditional")
    problem.add_fluent(is_same_obj, default_initial_value=False)
    problem.add_fluent(is_ok, default_initial_value=False)
    problem.add_fluent(is_ok_giver, default_initial_value=False)
    problem.add_fluent(ok_given, default_initial_value=False)
    problem.add_action(set_giver)
    problem.add_action(take_ok)
    problem.add_object(o1)
    problem.add_object(o2)
    problem.add_goal(is_ok(o1))
    problem.set_initial_value(is_same_obj(o1, o1), True)
    problem.set_initial_value(is_same_obj(o2, o2), True)
```

#### PDDL domain

```lisp
(define (domain temporal_conditional_domain)
 (:requirements :strips :typing :negative-preconditions :conditional-effects :durative-actions)
 (:types obj)
 (:predicates 
             (is_same_obj ?object_1 - obj ?object_2 - obj)
             (is_ok ?test - obj)
             (is_ok_giver ?test - obj)
             (ok_given)
 )
 (:durative-action set_giver
  :parameters ( ?param_y - obj)
  :duration (= ?duration 2)
  :condition (and 
                 (at start (not (is_ok_giver ?param_y)))
             )
  :effect (and
              (at start (is_ok_giver ?param_y))
              (at end (not (is_ok_giver ?param_y)))
          )
 )
 (:durative-action take_ok
  :parameters ( ?param_x - obj ?param_y - obj)
  :duration (= ?duration 3)
  :condition (and 
                 (at start (not (is_ok ?param_x)))
                 (at start (not (is_ok_giver ?param_y)))
                 (at start (not (is_same_obj ?param_x ?param_y)))
             )
  :effect (and
              (when (at end (is_ok_giver ?param_y)) (at end (is_ok ?param_x)))
              (at end (ok_given))
          )
 )
)
```

### basic_with_costs

This example defines `basic_with_costs` with 2 fluent(s), 3 action(s), and 0 object(s). Primary action(s): a, act_b, act_c. Goal summary: x. Special features: action costs, 1 quality metric(s).

#### unified-planning

```python
    # basic with actions cost
    x = Fluent("x")
    y = Fluent("y")
    act_a = InstantaneousAction("a")
    act_a.add_precondition(Not(x))
    act_a.add_effect(x, True)
    act_b = InstantaneousAction("act_b")
    act_b.add_precondition(Not(y))
    act_b.add_effect(y, True)
    act_c = InstantaneousAction("act_c")
    act_c.add_precondition(y)
    act_c.add_effect(x, True)
    problem = Problem("basic_with_costs")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(act_a)
    problem.add_action(act_b)
    problem.add_action(act_c)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y, False)
    problem.add_goal(x)
    problem.add_quality_metric(up.model.metrics.MinimizeActionCosts({act_a: Int(10), act_b: Int(1), act_c: Int(1)}))
```

#### PDDL domain

```lisp
(define (domain basic_with_costs_domain)
 (:requirements :strips :negative-preconditions :action-costs)
 (:predicates 
             (x)
             (y)
 )
 (:functions 
             (total-cost)
 )
 (:action a
  :parameters ()
  :precondition (and (not (x)))
  :effect (and (x) (increase (total-cost) 10)))
 (:action act_b
  :parameters ()
  :precondition (and (not (y)))
  :effect (and (y) (increase (total-cost) 1)))
 (:action act_c
  :parameters ()
  :precondition (and (y))
  :effect (and (x) (increase (total-cost) 1)))
)
```

### basic_with_default_values

This example defines `basic_with_default_values` with 3 fluent(s), 1 action(s), and 5 object(s). Primary action(s): a. Goal summary: g. Special features: object-valued fluents.

#### unified-planning

```python
    # basic with defaults
    problem = Problem("basic_with_default_values")
    object = UserType("object")
    objects = [problem.add_object(f"o{i}", object) for i in range(0, 5)]
    available = Fluent("available", BoolType(), a=object)

    on = Fluent("on", object, a=object)
    problem.add_fluent(available, default_initial_value=True)
    problem.add_fluent(on, default_initial_value=objects[0])
    goal = problem.add_fluent("g", default_initial_value=False)
    for i in [0, 1, 3, 4]:  # override default for all but objects[2]
        problem.set_initial_value(on(objects[i]), objects[4])
    act_a = InstantaneousAction("a", obj=object)
    act_a.add_precondition(available(objects[0]))
    act_a.add_precondition(Equals(on(act_a.obj), objects[0]))
    act_a.add_effect(goal, True)
    problem.add_action(act_a)
    problem.add_goal(goal)

```

#### PDDL domain

```text
PDDL domain export unavailable: PDDL supports only boolean and numerical fluents
```

### counter

This example defines `counter` with 3 fluent(s), 1 action(s), and 0 object(s). Primary action(s): increase. Goal summary: ((fake_counter < counter_1) iff (counter_2 < 3)). Special features: integer fluents, real fluents.

#### unified-planning

```python
    # counter
    counter_1 = Fluent("counter_1", IntType(0, 10))
    counter_2 = Fluent("counter_2", IntType(0, 10))
    fake_counter = Fluent("fake_counter", RealType(0, 10))
    increase = InstantaneousAction("increase")
    increase.add_increase_effect(counter_1, 1)
    increase.add_effect(counter_2, Plus(counter_2, 1))
    increase.add_effect(fake_counter, Div(Times(fake_counter, 2), 2))
    problem = Problem("counter")
    problem.add_fluent(counter_1)
    problem.add_fluent(counter_2)
    problem.add_fluent(fake_counter)
    problem.add_action(increase)
    problem.set_initial_value(counter_1, 0)
    problem.set_initial_value(counter_2, 0)
    problem.set_initial_value(fake_counter, 1)
    problem.add_goal(Iff(LT(fake_counter, counter_1), LT(counter_2, 3)))
```

#### PDDL domain

```lisp
(define (domain counter_domain)
 (:requirements :strips :numeric-fluents)
 (:functions 
             (counter_1)
             (counter_2)
             (fake_counter)
 )
 (:action increase_
  :parameters ()
  :effect (and (increase (counter_1) 1) (assign (counter_2) (+ 1 (counter_2))) (assign (fake_counter) (/ (* 2 (fake_counter)) 2))))
)
```

### counter_to_50

This example defines `counter_to_50` with 1 fluent(s), 1 action(s), and 0 object(s). Primary action(s): increase. Goal summary: (counter == 50). Special features: integer fluents.

#### unified-planning

```python
    # counter to 50
    counter_f = Fluent("counter", IntType(0, 100))
    increase = InstantaneousAction("increase")
    increase.add_increase_effect(counter_f, 1)
    problem = Problem("counter_to_50")
    problem.add_fluent(counter_f)
    problem.add_action(increase)
    problem.set_initial_value(counter_f, 0)
    problem.add_goal(Equals(counter_f, 50))
```

#### PDDL domain

```lisp
(define (domain counter_to_50_domain)
 (:requirements :strips :equality :numeric-fluents)
 (:functions 
             (counter)
 )
 (:action increase_
  :parameters ()
  :effect (and (increase (counter) 1)))
)
```

### temporal_counter

This example defines `temporal_counter` with 1 fluent(s), 2 action(s), and 0 object(s). Primary action(s): increase, decrease. Goal summary: (counter == 1). Special features: continuous time, integer fluents.

#### unified-planning

```python
    # temporal counter
    counter_f = Fluent("counter", IntType(0, 100))
    d_increase = DurativeAction("increase")
    d_increase.set_fixed_duration(1)
    d_increase.add_condition(StartTiming(), LT(counter_f, 99))
    d_increase.add_increase_effect(EndTiming(), counter_f, 2)
    d_decrease = DurativeAction("decrease")
    d_decrease.set_fixed_duration(1)
    d_decrease.add_condition(StartTiming(), GT(counter_f, 0))
    d_decrease.add_decrease_effect(EndTiming(), counter_f, 1)
    problem = Problem("temporal_counter")
    problem.add_fluent(counter_f)
    problem.add_action(d_increase)
    problem.add_action(d_decrease)
    problem.set_initial_value(counter_f, 0)
    problem.add_goal(Equals(counter_f, 1))
```

#### PDDL domain

```lisp
(define (domain temporal_counter_domain)
 (:requirements :strips :equality :numeric-fluents :durative-actions)
 (:functions 
             (counter)
 )
 (:durative-action increase_
  :parameters ()
  :duration (= ?duration 1)
  :condition (and 
                 (at start (< (counter) 99))
             )
  :effect (and
              (at end (increase (counter) 2))
          )
 )
 (:durative-action decrease_
  :parameters ()
  :duration (= ?duration 1)
  :condition (and 
                 (at start (< 0 (counter)))
             )
  :effect (and
              (at end (decrease (counter) 1))
          )
 )
)
```

### basic_with_object_constant

This example defines `basic_with_object_constant` with 1 fluent(s), 2 action(s), and 2 object(s). Primary action(s): move, move_to_l1. Goal summary: is_at(l2). Special features: classical planning only.

#### unified-planning

```python
    # basic with object constant
    Location = UserType("Location")
    is_at = Fluent("is_at", BoolType(), loc=Location)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(is_at(l_from))
    move.add_precondition(Not(is_at(l_to)))
    move.add_effect(is_at(l_from), False)
    move.add_effect(is_at(l_to), True)
    move_to_l1 = InstantaneousAction("move_to_l1", l_from=Location)
    l_from = move_to_l1.parameter("l_from")
    move_to_l1.add_precondition(is_at(l_from))
    move_to_l1.add_precondition(Not(is_at(l1)))
    move_to_l1.add_effect(is_at(l_from), False)
    move_to_l1.add_effect(is_at(l1), True)
    problem = Problem("basic_with_object_constant")
    problem.add_fluent(is_at)
    problem.add_objects([l1, l2])
    problem.add_action(move)
    problem.add_action(move_to_l1)
    problem.set_initial_value(is_at(l1), True)
    problem.set_initial_value(is_at(l2), False)
    problem.add_goal(is_at(l2))
```

#### PDDL domain

```lisp
(define (domain basic_with_object_constant_domain)
 (:requirements :strips :typing :negative-preconditions)
 (:types location)
 (:constants
   l1 - location
 )
 (:predicates 
             (is_at ?loc - location)
 )
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and (is_at ?l_from) (not (is_at ?l_to)))
  :effect (and (not (is_at ?l_from)) (is_at ?l_to)))
 (:action move_to_l1
  :parameters ( ?l_from - location)
  :precondition (and (is_at ?l_from) (not (is_at l1)))
  :effect (and (not (is_at ?l_from)) (is_at l1)))
)
```

### basic_numeric

This example defines `basic_numeric` with 1 fluent(s), 1 action(s), and 0 object(s). Primary action(s): task. Goal summary: (value == 2). Special features: integer fluents.

#### unified-planning

```python
    # basic numeric
    value = Fluent("value", IntType())
    task = InstantaneousAction("task")
    task.add_precondition(Equals(value, 1))
    task.add_effect(value, 2)
    problem = Problem("basic_numeric")
    problem.add_fluent(value)
    problem.add_action(task)
    problem.set_initial_value(value, 1)
    problem.add_goal(Equals(value, 2))
```

#### PDDL domain

```lisp
(define (domain basic_numeric_domain)
 (:requirements :strips :equality :numeric-fluents)
 (:functions 
             (value)
 )
 (:action task
  :parameters ()
  :precondition (and (= (value) 1))
  :effect (and (assign (value) 2)))
)
```

### basic_numeric_with_timed_effect

This example defines `basic_numeric_with_timed_effect` with 1 fluent(s), 1 action(s), and 0 object(s). Primary action(s): task. Goal summary: (value == 2). Special features: continuous time, timed effects, integer fluents.

#### unified-planning

```python
    # basic numeric with timed effect
    value = Fluent("value", IntType())
    task = InstantaneousAction("task")
    task.add_precondition(Equals(value, 1))
    task.add_effect(value, 2)
    problem = Problem("basic_numeric_with_timed_effect")
    problem.add_fluent(value)
    problem.add_action(task)
    problem.set_initial_value(value, 1)
    problem.add_goal(Equals(value, 2))
    problem.add_timed_effect(GlobalStartTiming(1), value, 1)
```

#### PDDL domain

```lisp
(define (domain basic_numeric_with_timed_effect_domain)
 (:requirements :strips :equality :numeric-fluents :durative-actions :timed-initial-effects)
 (:functions 
             (value)
 )
 (:action task
  :parameters ()
  :precondition (and (= (value) 1))
  :effect (and (assign (value) 2)))
)
```

### basic_undef_bool

This example defines `basic_undef_bool` with 2 fluent(s), 2 action(s), and 0 object(s). Primary action(s): a1, set_b. Goal summary: fluent1. Special features: classical planning only.

#### unified-planning

```python
    # basic with undefined initial symbolic
    problem = Problem("basic_undef_bool")
    fluent1 = problem.add_fluent("fluent1", BoolType())
    problem.set_initial_value(fluent1(), False)
    fluent2 = problem.add_fluent("fluent2", BoolType())
    problem.add_goal(fluent1())

    a1 = InstantaneousAction("a1")
    a1.add_precondition(Not(fluent1()))
    a1.add_effect(fluent1(), True)
    problem.add_action(a1)
    a2 = InstantaneousAction("set_b")
    a2.add_precondition(
        Or(Not(fluent1()), Not(fluent2()))
    )  # never valid under PDDL semantics as fluent2() is undefined
    a2.add_effect(fluent1(), True)
    problem.add_action(a2)
```

#### PDDL domain

```lisp
(define (domain basic_undef_bool_domain)
 (:requirements :strips :negative-preconditions :disjunctive-preconditions)
 (:predicates 
             (fluent1)
             (fluent2)
 )
 (:action a1
  :parameters ()
  :precondition (and (not (fluent1)))
  :effect (and (fluent1)))
 (:action set_b
  :parameters ()
  :precondition (and (or (not (fluent1)) (not (fluent2))))
  :effect (and (fluent1)))
)
```

### basic_undef_numeric

This example defines `basic_undef_numeric` with 1 fluent(s), 2 action(s), and 2 object(s). Primary action(s): increase_one, increase_both. Goal summary: (value(o1) == 1). Special features: integer fluents.

#### unified-planning

```python
    # basic numeric with undefined initial value
    problem = Problem("basic_undef_numeric")
    object_type = UserType("Obj")
    o1 = problem.add_object("o1", object_type)
    o2 = problem.add_object("o2", object_type)
    value = problem.add_fluent("value", IntType(), o=object_type)
    problem.set_initial_value(value(o1), 0)  # only value(o1) is defined
    increase_one = InstantaneousAction("increase_one", o=object_type)
    increase_one.add_increase_effect(value(increase_one.o), 1)
    problem.add_action(increase_one)

    increase_both = InstantaneousAction("increase_both")
    increase_both.add_increase_effect(value(o1), 1)
    increase_both.add_increase_effect(value(o2), 1)
    problem.add_action(increase_both)

    problem.add_goal(Equals(value(o1), 1))
```

#### PDDL domain

```lisp
(define (domain basic_undef_numeric_domain)
 (:requirements :strips :typing :equality :numeric-fluents)
 (:types obj)
 (:constants
   o2 o1 - obj
 )
 (:functions 
             (value ?o - obj)
 )
 (:action increase_one
  :parameters ( ?o - obj)
  :effect (and (increase (value ?o) 1)))
 (:action increase_both
  :parameters ()
  :effect (and (increase (value o1) 1) (increase (value o2) 1)))
)
```

### undef_numeric_with_timed_effects

This example defines `undef_numeric_with_timed_effects` with 1 fluent(s), 2 action(s), and 2 object(s). Primary action(s): increase_one, increase_both. Goal summary: (value(o1) == 2); (value(o2) == 2). Special features: continuous time, conditional effects, timed effects, timed goals, integer fluents.

#### unified-planning

```python
    # numeric with timed effect and undefined initial value
    problem = Problem("undef_numeric_with_timed_effects")
    object_type = UserType("Obj")
    o1 = problem.add_object("o1", object_type)
    o2 = problem.add_object("o2", object_type)
    value = problem.add_fluent("value", IntType(), o=object_type)
    problem.set_initial_value(value(o1), 1)  # only value(o1) is defined

    increase_one_durative = DurativeAction("increase_one", o=object_type)
    increase_one_durative.set_fixed_duration(2)
    increase_one_durative.add_increase_effect(
        EndTiming(),
        value(increase_one_durative.o),
        1,
        LT(value(increase_one_durative.o), 2),
    )
    problem.add_action(increase_one_durative)

    increase_both = InstantaneousAction("increase_both")
    increase_both.add_increase_effect(value(o1), 1)
    increase_both.add_increase_effect(value(o2), 1)
    problem.add_action(increase_both)

    problem.add_timed_effect(GlobalStartTiming(1), value(o2), 1)
    problem.add_timed_goal(
        ClosedTimeInterval(GlobalStartTiming(2), GlobalStartTiming(3)),
        And(Equals(value(o1), 2), Equals(value(o2), 2)),
    )

    problem.add_goal(Equals(value(o1), 2))
    problem.add_goal(Equals(value(o2), 2))
```

#### PDDL domain

```text
PDDL domain export unavailable: PDDL does not support timed goals.
```

### durative_continuous_example

This example defines `durative_continuous_example` with 1 fluent(s), 1 action(s), and 0 object(s). Primary action(s): continuous_change. Goal summary: (20 <= continous_changing_fluent). Special features: continuous time, real fluents.

#### unified-planning

```python
    # continuous effect in durative
    continous_changing_fluent = Fluent("continous_changing_fluent", RealType())

    continuous_change = DurativeAction("continuous_change")
    interval = TimeInterval(StartTiming(), EndTiming())
    continuous_change.add_increase_continuous_effect(interval, continous_changing_fluent, 1)
    continuous_change.add_condition(StartTiming(), LE(continous_changing_fluent, 30))

    problem = Problem("durative_continuous_example")
    problem.add_fluent(continous_changing_fluent)
    problem.add_action(continuous_change)
    problem.set_initial_value(continous_changing_fluent, 5)
    problem.add_goal(GE(continous_changing_fluent, 20))

```

#### PDDL domain

```lisp
(define (domain durative_continuous_example_domain)
 (:requirements :strips :numeric-fluents :durative-actions :continuous-effects)
 (:functions 
             (continous_changing_fluent)
 )
 (:durative-action continuous_change
  :parameters ()
  :duration (= ?duration 0)
  :condition (and 
                 (at start (<= (continous_changing_fluent) 30))
             )
  :effect (and
 (increase (continous_changing_fluent) (* #t 1))
          )
 )
)
```
## variants

### Problems

- [basic_bool_fluent_param](#basic_bool_fluent_param)
- [basic_int_fluent_param](#basic_int_fluent_param)
- [basic_bounded_int_action_param](#basic_bounded_int_action_param)
- [basic_unbounded_int_action_param](#basic_unbounded_int_action_param)
- [robot_real_constants](#robot_real_constants)
- [robot_int_battery](#robot_int_battery)
- [robot_fluent_of_user_type_with_int_id](#robot_fluent_of_user_type_with_int_id)
- [robot_locations_connected_without_battery](#robot_locations_connected_without_battery)
- [robot_loader_weak_bridge](#robot_loader_weak_bridge)
- [robot_with_variable_duration](#robot_with_variable_duration)
- [hierarchical_blocks_world_exists](#hierarchical_blocks_world_exists)
- [hierarchical_blocks_world_object_as_root](#hierarchical_blocks_world_object_as_root)
- [hierarchical_blocks_world_with_object](#hierarchical_blocks_world_with_object)
- [travel_with_consumptions](#travel_with_consumptions)
- [matchcellar_static_duration](#matchcellar_static_duration)
- [locations_connected_visited_oversubscription](#locations_connected_visited_oversubscription)
- [locations_connected_cost_minimize](#locations_connected_cost_minimize)
- [robot_conditional_effects](#robot_conditional_effects)
- [robot_non_linear_continuous_1](#robot_non_linear_continuous_1)

### basic_bool_fluent_param

This example defines `basic_bool_fluent_param` with 1 fluent(s), 1 action(s), and 0 object(s). Primary action(s): a. Goal summary: (x(true) and x(false)). Special features: classical planning only.

#### unified-planning

```python
    # basic_bool_fluent_param
    x = Fluent("x", int_param=BoolType())
    a = InstantaneousAction("a")
    a.add_precondition(Not(x(True)))
    a.add_effect(x(True), True)
    problem = Problem("basic_bool_fluent_param")
    problem.add_fluent(x, default_initial_value=False)
    problem.add_action(a)
    problem.set_initial_value(x(False), True)
    problem.add_goal(And(x(True), x(False)))
```

#### PDDL domain

```text
PDDL domain export unavailable: PDDL supports only user type parameters
```

### basic_int_fluent_param

This example defines `basic_int_fluent_param` with 1 fluent(s), 1 action(s), and 0 object(s). Primary action(s): a. Goal summary: (x(3) and x(4) and (not x(5))). Special features: classical planning only.

#### unified-planning

```python
    # basic_int_fluent_param
    int_3_6 = IntType(3, 6)
    x = Fluent("x", int_param=int_3_6)
    a = InstantaneousAction("a")
    a.add_precondition(Not(x(3)))
    a.add_effect(x(3), True)
    problem = Problem("basic_int_fluent_param")
    problem.add_fluent(x, default_initial_value=False)
    problem.add_action(a)
    problem.set_initial_value(x(4), True)
    problem.add_goal(And(x(3), x(4), Not(x(5))))
```

#### PDDL domain

```text
PDDL domain export unavailable: PDDL supports only user type parameters
```

### basic_bounded_int_action_param

This example defines `basic_bounded_int_action_param` with 1 fluent(s), 1 action(s), and 0 object(s). Primary action(s): a. Goal summary: (x(3) and x(4) and (not x(5))). Special features: classical planning only.

#### unified-planning

```python
    # basic_bounded_int_action_param
    int_3_6 = IntType(3, 6)
    x = Fluent("x", int_param=int_3_6)
    a = InstantaneousAction("a", int_param=int_3_6)
    a.add_precondition(Not(x(a.int_param)))
    a.add_effect(x(a.int_param), True)
    problem = Problem("basic_bounded_int_action_param")
    problem.add_fluent(x, default_initial_value=False)
    problem.add_action(a)
    problem.add_goal(And(x(3), x(4), Not(x(5))))
```

#### PDDL domain

```text
PDDL domain export unavailable: PDDL supports only user type parameters
```

### basic_unbounded_int_action_param

This example defines `basic_unbounded_int_action_param` with 1 fluent(s), 1 action(s), and 0 object(s). Primary action(s): a. Goal summary: (x(3) and x(4) and (not x(5))). Special features: classical planning only.

#### unified-planning

```python
    # basic_unbounded_int_action_param
    int_3_6 = IntType(3, 6)
    int_3 = IntType(3)
    x = Fluent("x", int_param=int_3_6)
    a = InstantaneousAction("a", int_param=int_3)
    a.add_precondition(Not(x(a.int_param)))
    a.add_effect(x(a.int_param), True)
    problem = Problem("basic_unbounded_int_action_param")
    problem.add_fluent(x, default_initial_value=False)
    problem.add_action(a)
    problem.add_goal(And(x(3), x(4), Not(x(5))))
```

#### PDDL domain

```text
PDDL domain export unavailable: PDDL supports only user type parameters
```

### robot_real_constants

This example defines `robot_real_constants` with 2 fluent(s), 1 action(s), and 2 object(s). Primary action(s): move. Goal summary: robot_at(l2). Special features: real fluents.

#### unified-planning

```python
    # robot_real_constants
    # this version of the problem robot has reals instead of integers as constants
    Location = UserType("Location")
    robot_at = Fluent("robot_at", BoolType(), position=Location)
    battery_charge = Fluent("battery_charge", RealType(0, 100))
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(GE(battery_charge, 10.0))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    move.add_effect(battery_charge, Minus(battery_charge, 10.0))
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot_real_constants")
    problem.add_fluent(robot_at)
    problem.add_fluent(battery_charge)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(battery_charge, 100.0)
    problem.add_goal(robot_at(l2))
```

#### PDDL domain

```lisp
(define (domain robot_real_constants_domain)
 (:requirements :strips :typing :negative-preconditions :equality :numeric-fluents)
 (:types location)
 (:predicates 
             (robot_at ?position - location)
 )
 (:functions 
             (battery_charge)
 )
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and (<= 10 (battery_charge)) (not (= ?l_from ?l_to)) (robot_at ?l_from) (not (robot_at ?l_to)))
  :effect (and (not (robot_at ?l_from)) (robot_at ?l_to) (assign (battery_charge) (- (battery_charge) 10))))
)
```

### robot_int_battery

This example defines `robot_int_battery` with 2 fluent(s), 1 action(s), and 2 object(s). Primary action(s): move. Goal summary: robot_at(l2). Special features: integer fluents.

#### unified-planning

```python
    # robot_int_battery
    # this version of the problem robot has the battery charge fluent represented as an int instead of a real
    Location = UserType("Location")
    robot_at = Fluent("robot_at", BoolType(), position=Location)
    battery_charge = Fluent("battery_charge", IntType(0, 100))
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(GE(battery_charge, 10))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    move.add_effect(battery_charge, Minus(battery_charge, 10))
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot_int_battery")
    problem.add_fluent(robot_at)
    problem.add_fluent(battery_charge)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(battery_charge, 100)
    problem.add_goal(robot_at(l2))
```

#### PDDL domain

```lisp
(define (domain robot_int_battery_domain)
 (:requirements :strips :typing :negative-preconditions :equality :numeric-fluents)
 (:types location)
 (:predicates 
             (robot_at ?position - location)
 )
 (:functions 
             (battery_charge)
 )
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and (<= 10 (battery_charge)) (not (= ?l_from ?l_to)) (robot_at ?l_from) (not (robot_at ?l_to)))
  :effect (and (not (robot_at ?l_from)) (robot_at ?l_to) (assign (battery_charge) (- (battery_charge) 10))))
)
```

### robot_fluent_of_user_type_with_int_id

This example defines `robot_fluent_of_user_type_with_int_id` with 1 fluent(s), 1 action(s), and 2 object(s). Primary action(s): move. Goal summary: (is_at(0) == l2); (is_at(1) == l2). Special features: object-valued fluents.

#### unified-planning

```python
    # robot fluent of user_type with int ID
    Int_t = IntType(0, 1)
    Location = UserType("Location")
    is_at = Fluent("is_at", Location, id=Int_t)
    move = InstantaneousAction("move", robot=Int_t, l_from=Location, l_to=Location)
    robot = move.parameter("robot")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(Equals(is_at(robot), l_from))
    move.add_precondition(Not(Equals(is_at(robot), l_to)))
    move.add_effect(is_at(robot), l_to)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot_fluent_of_user_type_with_int_id")
    problem.add_fluent(is_at)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(is_at(Int(0)), l1)
    problem.set_initial_value(is_at(1), l1)
    problem.add_goal(is_at(0).Equals(l2))
    problem.add_goal(is_at(1).Equals(l2))
```

#### PDDL domain

```text
PDDL domain export unavailable: PDDL supports only boolean and numerical fluents
```

### robot_locations_connected_without_battery

This example defines `robot_locations_connected_without_battery` with 2 fluent(s), 2 action(s), and 6 object(s). Primary action(s): move, move_2. Goal summary: is_at(l5, r1). Special features: existential conditions.

#### unified-planning

```python
    # robot locations connected without battery
    Location = UserType("Location")
    Robot = UserType("Robot")
    is_at = Fluent("is_at", BoolType(), position=Location, robot=Robot)
    is_connected = Fluent("is_connected", BoolType(), location_1=Location, location_2=Location)
    move = InstantaneousAction("move", robot=Robot, l_from=Location, l_to=Location)
    robot = move.parameter("robot")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(is_at(l_from, robot))
    move.add_precondition(Not(is_at(l_to, robot)))
    move.add_precondition(Or(is_connected(l_from, l_to), is_connected(l_to, l_from)))
    move.add_effect(is_at(l_from, robot), False)
    move.add_effect(is_at(l_to, robot), True)
    move_2 = InstantaneousAction("move_2", robot=Robot, l_from=Location, l_to=Location)
    robot = move_2.parameter("robot")
    l_from = move_2.parameter("l_from")
    l_to = move_2.parameter("l_to")
    move_2.add_precondition(Not(Equals(l_from, l_to)))
    move_2.add_precondition(is_at(l_from, robot))
    move_2.add_precondition(Not(is_at(l_to, robot)))
    mid_location = Variable("mid_loc", Location)
    # (E (location mid_location)
    # !((mid_location == l_from) || (mid_location == l_to)) && (is_connected(l_from, mid_location) || is_connected(mid_location, l_from)) &&
    # && (is_connected(l_to, mid_location) || is_connected(mid_location, l_to)))
    move_2.add_precondition(
        Exists(
            And(
                Not(Or(Equals(mid_location, l_from), Equals(mid_location, l_to))),
                Or(
                    is_connected(l_from, mid_location),
                    is_connected(mid_location, l_from),
                ),
                Or(is_connected(l_to, mid_location), is_connected(mid_location, l_to)),
            ),
            mid_location,
        )
    )
    move_2.add_effect(is_at(l_from, robot), False)
    move_2.add_effect(is_at(l_to, robot), True)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    r1 = Object("r1", Robot)
    problem = Problem("robot_locations_connected_without_battery")
    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_action(move)
    problem.add_action(move_2)
    problem.add_object(r1)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(l3)
    problem.add_object(l4)
    problem.add_object(l5)
    problem.set_initial_value(is_at(l1, r1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.add_goal(is_at(l5, r1))
```

#### PDDL domain

```lisp
(define (domain robot_locations_connected_without_battery_domain)
 (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :equality :existential-preconditions)
 (:types location robot)
 (:predicates 
             (is_at ?position - location ?robot - robot)
             (is_connected ?location_1 - location ?location_2 - location)
 )
 (:action move
  :parameters ( ?robot - robot ?l_from - location ?l_to - location)
  :precondition (and (not (= ?l_from ?l_to)) (is_at ?l_from ?robot) (not (is_at ?l_to ?robot)) (or (is_connected ?l_from ?l_to) (is_connected ?l_to ?l_from)))
  :effect (and (not (is_at ?l_from ?robot)) (is_at ?l_to ?robot)))
 (:action move_2
  :parameters ( ?robot - robot ?l_from - location ?l_to - location)
  :precondition (and (not (= ?l_from ?l_to)) (is_at ?l_from ?robot) (not (is_at ?l_to ?robot)) (exists (?mid_loc - location)
 (and (not (or (= ?mid_loc ?l_from) (= ?mid_loc ?l_to))) (or (is_connected ?l_from ?mid_loc) (is_connected ?mid_loc ?l_from)) (or (is_connected ?l_to ?mid_loc) (is_connected ?mid_loc ?l_to)))))
  :effect (and (not (is_at ?l_from ?robot)) (is_at ?l_to ?robot)))
)
```

### robot_loader_weak_bridge

This example defines `robot_loader_weak_bridge` with 5 fluent(s), 3 action(s), and 3 object(s). Primary action(s): move, load, unload. Goal summary: cargo_at(l1). Special features: state invariants.

#### unified-planning

```python
    # robot_loader_weak_bridge
    # version of robot loader with weak bridges that can't be crossed with
    # the cargo loaded. Uses global_constraints.
    Location = UserType("Location")
    locations = [Object(f"l{i}", Location) for i in range(1, 4)]
    l1, l2, l3 = locations
    robot_is_at = Fluent("robot_is_at", BoolType(), position=Location)
    robot_was_at = Fluent("robot_was_at", BoolType(), past_position=Location)
    cargo_at = Fluent("cargo_at", BoolType(), position=Location)
    cargo_mounted = Fluent("cargo_mounted")
    weak_bridge = Fluent("weak_bridge", BoolType(), l_from=Location, l_to=Location)

    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_is_at(l_from))
    move.add_precondition(Not(robot_is_at(l_to)))
    move.add_effect(robot_is_at(l_from), False)
    move.add_effect(robot_is_at(l_to), True)
    move.add_effect(robot_was_at(l_from), True)
    for l_obj in locations:  # note that this works for the add-after-delete semantic
        move.add_effect(robot_was_at(l_obj), False)

    load = InstantaneousAction("load", loc=Location)
    loc = load.parameter("loc")
    load.add_precondition(cargo_at(loc))
    load.add_precondition(robot_is_at(loc))
    load.add_precondition(Not(cargo_mounted))
    load.add_effect(cargo_at(loc), False)
    load.add_effect(cargo_mounted, True)
    load.add_effect(robot_was_at(loc), True)
    for l_obj in locations:
        load.add_effect(robot_was_at(l_obj), False)

    unload = InstantaneousAction("unload", loc=Location)
    loc = unload.parameter("loc")
    unload.add_precondition(Not(cargo_at(loc)))
    unload.add_precondition(robot_is_at(loc))
    unload.add_precondition(cargo_mounted)
    unload.add_effect(cargo_at(loc), True)
    unload.add_effect(cargo_mounted, False)
    unload.add_effect(robot_was_at(loc), True)
    for l_obj in locations:
        unload.add_effect(robot_was_at(l_obj), False)

    problem = Problem("robot_loader_weak_bridge")
    problem.add_fluent(robot_is_at, default_initial_value=False)
    problem.add_fluent(robot_was_at, default_initial_value=False)
    problem.add_fluent(cargo_at, default_initial_value=False)
    problem.add_fluent(cargo_mounted, default_initial_value=False)
    problem.add_fluent(weak_bridge, default_initial_value=False)
    problem.add_action(move)
    problem.add_action(load)
    problem.add_action(unload)
    problem.add_objects(locations)
    problem.set_initial_value(robot_is_at(l1), True)
    problem.set_initial_value(robot_was_at(l1), True)
    problem.set_initial_value(cargo_at(l3), True)
    problem.set_initial_value(weak_bridge(l3, l1), True)
    problem.set_initial_value(weak_bridge(l1, l3), True)
    problem.add_goal(cargo_at(l1))
    # for all the possible couples of locations, it must never be True that:
    # The robot is loaded when crossing a weak bridge.
    for l_from_v, l_to_v in product(locations, repeat=2):
        problem.add_state_invariant(
            Not(
                And(
                    weak_bridge(l_from_v, l_to_v),
                    robot_was_at(l_from_v),
                    robot_is_at(l_to_v),
                    cargo_mounted,
                )
            )
        )
```

#### PDDL domain

```lisp
(define (domain robot_loader_weak_bridge_domain)
 (:requirements :strips :typing :negative-preconditions :equality :constraints)
 (:types location)
 (:constants
   l2 l1 l3 - location
 )
 (:predicates 
             (robot_is_at ?position - location)
             (robot_was_at ?past_position - location)
             (cargo_at ?position - location)
             (cargo_mounted)
             (weak_bridge ?l_from - location ?l_to - location)
 )
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and (not (= ?l_from ?l_to)) (robot_is_at ?l_from) (not (robot_is_at ?l_to)))
  :effect (and (not (robot_is_at ?l_from)) (robot_is_at ?l_to) (robot_was_at ?l_from) (not (robot_was_at l1)) (not (robot_was_at l2)) (not (robot_was_at l3))))
 (:action load
  :parameters ( ?loc - location)
  :precondition (and (cargo_at ?loc) (robot_is_at ?loc) (not (cargo_mounted)))
  :effect (and (not (cargo_at ?loc)) (cargo_mounted) (robot_was_at ?loc) (not (robot_was_at l1)) (not (robot_was_at l2)) (not (robot_was_at l3))))
 (:action unload
  :parameters ( ?loc - location)
  :precondition (and (not (cargo_at ?loc)) (robot_is_at ?loc) (cargo_mounted))
  :effect (and (cargo_at ?loc) (not (cargo_mounted)) (robot_was_at ?loc) (not (robot_was_at l1)) (not (robot_was_at l2)) (not (robot_was_at l3))))
)
```

### robot_with_variable_duration

This example defines `robot_with_variable_duration` with 3 fluent(s), 1 action(s), and 6 object(s). Primary action(s): move. Goal summary: is_at(l5, r1). Special features: continuous time.

#### unified-planning

```python
    # robot with variable duration. the variants have different constraints on the action duration
    problem = Problem("robot_with_variable_duration")
    Location = UserType("Location")
    Robot = UserType("Robot")

    is_at = Fluent("is_at", BoolType(), position=Location, robot=Robot)
    is_connected = Fluent("is_connected", BoolType(), l_from=Location, l_to=Location)
    distance = Fluent("distance", RealType(), l_from=Location, l_to=Location)
    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_fluent(distance, default_initial_value=1)

    r1 = Object("r1", Robot)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    problem.add_objects([r1, l1, l2, l3, l4, l5])

    problem.set_initial_value(is_at(l1, r1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.set_initial_value(distance(l1, l2), 10)
    problem.set_initial_value(distance(l2, l3), 10)
    problem.set_initial_value(distance(l3, l4), 10)
    problem.set_initial_value(distance(l4, l5), 10)
    problem.add_goal(is_at(l5, r1))

    dur_move = DurativeAction("move", r=Robot, l_from=Location, l_to=Location)
    r = dur_move.parameter("r")
    l_from = dur_move.parameter("l_from")
    l_to = dur_move.parameter("l_to")
    dur_move.add_condition(StartTiming(), is_connected(l_from, l_to))
    dur_move.add_condition(StartTiming(), is_at(l_from, r))
    dur_move.add_condition(StartTiming(), Not(is_at(l_to, r)))
    dur_move.add_effect(StartTiming(), is_at(l_from, r), False)
    dur_move.add_effect(EndTiming(), is_at(l_to, r), True)
    dur_move.set_duration_constraint(ClosedDurationInterval(Int(5), Int(7)))
    problem.add_action(dur_move)
```

#### PDDL domain

```lisp
(define (domain robot_with_variable_duration_domain)
 (:requirements :strips :typing :negative-preconditions :durative-actions :duration-inequalities)
 (:types location robot)
 (:predicates 
             (is_at ?position - location ?robot - robot)
             (is_connected ?l_from - location ?l_to - location)
 )
 (:functions 
             (distance ?l_from - location ?l_to - location)
 )
 (:durative-action move
  :parameters ( ?r - robot ?l_from - location ?l_to - location)
  :duration (and (>= ?duration 5)(<= ?duration 7))
  :condition (and 
                 (at start (is_connected ?l_from ?l_to))
                 (at start (is_at ?l_from ?r))
                 (at start (not (is_at ?l_to ?r)))
             )
  :effect (and
              (at start (not (is_at ?l_from ?r)))
              (at end (is_at ?l_to ?r))
          )
 )
)
```

### hierarchical_blocks_world_exists

This example defines `hierarchical_blocks_world_exists` with 2 fluent(s), 1 action(s), and 6 object(s). Primary action(s): move. Goal summary: on(block_1, ts_3); Exists (Movable - Location m_var) on(m_var, block_1); .... Special features: existential conditions.

#### unified-planning

```python
    # hierarchical blocks world exists
    Entity = UserType("Entity", None)  # None can be avoided
    Location = UserType("Location", Entity)
    Unmovable = UserType("Unmovable", Location)
    TableSpace = UserType("TableSpace", Unmovable)
    Movable = UserType("Movable", Location)
    Block = UserType("Block", Movable)
    clear = Fluent("clear", BoolType(), space=Location)
    on = Fluent("on", BoolType(), object=Movable, space=Location)

    move = InstantaneousAction("move", item=Movable, l_from=Location, l_to=Location)
    item = move.parameter("item")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(clear(item))
    move.add_precondition(clear(l_to))
    move.add_precondition(on(item, l_from))
    move.add_effect(clear(l_from), True)
    move.add_effect(on(item, l_from), False)
    move.add_effect(clear(l_to), False)
    move.add_effect(on(item, l_to), True)

    problem = Problem("hierarchical_blocks_world_exists")
    problem.add_fluent(clear, default_initial_value=False)
    problem.add_fluent(on, default_initial_value=False)
    problem.add_action(move)
    ts_1 = Object("ts_1", TableSpace)
    ts_2 = Object("ts_2", TableSpace)
    ts_3 = Object("ts_3", TableSpace)
    problem.add_objects([ts_1, ts_2, ts_3])
    block_1 = Object("block_1", Block)
    block_2 = Object("block_2", Block)
    block_3 = Object("block_3", Block)
    problem.add_objects([block_1, block_2, block_3])

    # The blocks are all on ts_1, in order block_3 under block_1 under block_2
    problem.set_initial_value(clear(ts_2), True)
    problem.set_initial_value(clear(ts_3), True)
    problem.set_initial_value(clear(block_2), True)
    problem.set_initial_value(on(block_3, ts_1), True)
    problem.set_initial_value(on(block_1, block_3), True)
    problem.set_initial_value(on(block_2, block_1), True)

    # We want them on ts_3 in order block_3 on block_2 on block_1
    problem.add_goal(on(block_1, ts_3))
    m_var = Variable("m_var", Movable)
    problem.add_goal(Exists(on(m_var, block_1), m_var))
    problem.add_goal(on(block_3, block_2))

```

#### PDDL domain

```lisp
(define (domain hierarchical_blocks_world_exists_domain)
 (:requirements :strips :typing :existential-preconditions)
 (:types
    entity - object
    location - entity
    movable unmovable - location
    tablespace - unmovable
    block - movable
 )
 (:predicates 
             (clear ?space - location)
             (on ?object - movable ?space - location)
 )
 (:action move
  :parameters ( ?item - movable ?l_from - location ?l_to - location)
  :precondition (and (clear ?item) (clear ?l_to) (on ?item ?l_from))
  :effect (and (clear ?l_from) (not (on ?item ?l_from)) (not (clear ?l_to)) (on ?item ?l_to)))
)
```

### hierarchical_blocks_world_object_as_root

This example defines `hierarchical_blocks_world_object_as_root` with 2 fluent(s), 1 action(s), and 6 object(s). Primary action(s): move. Goal summary: on(block_1, ts_3); on(block_2, block_1); .... Special features: classical planning only.

#### unified-planning

```python
    # hierarchical blocks world object as root
    object = UserType("object")
    Entity = UserType("Entity", object)
    Location = UserType("Location", Entity)
    Unmovable = UserType("Unmovable", Location)
    TableSpace = UserType("TableSpace", Unmovable)
    Movable = UserType("Movable", Location)
    Block = UserType("Block", Movable)
    clear = Fluent("clear", BoolType(), space=Location)
    on = Fluent("on", BoolType(), object=Movable, space=Location)

    move = InstantaneousAction("move", item=Movable, l_from=Location, l_to=Location)
    item = move.parameter("item")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(clear(item))
    move.add_precondition(clear(l_to))
    move.add_precondition(on(item, l_from))
    move.add_effect(clear(l_from), True)
    move.add_effect(on(item, l_from), False)
    move.add_effect(clear(l_to), False)
    move.add_effect(on(item, l_to), True)

    problem = Problem("hierarchical_blocks_world_object_as_root")
    problem.add_fluent(clear, default_initial_value=False)
    problem.add_fluent(on, default_initial_value=False)
    problem.add_action(move)
    ts_1 = Object("ts_1", TableSpace)
    ts_2 = Object("ts_2", TableSpace)
    ts_3 = Object("ts_3", TableSpace)
    problem.add_objects([ts_1, ts_2, ts_3])
    block_1 = Object("block_1", Block)
    block_2 = Object("block_2", Block)
    block_3 = Object("block_3", Block)
    problem.add_objects([block_1, block_2, block_3])

    # The blocks are all on ts_1, in order block_3 under block_1 under block_2
    problem.set_initial_value(clear(ts_2), True)
    problem.set_initial_value(clear(ts_3), True)
    problem.set_initial_value(clear(block_2), True)
    problem.set_initial_value(on(block_3, ts_1), True)
    problem.set_initial_value(on(block_1, block_3), True)
    problem.set_initial_value(on(block_2, block_1), True)

    # We want them on ts_3 in order block_3 on block_2 on block_1
    problem.add_goal(on(block_1, ts_3))
    problem.add_goal(on(block_2, block_1))
    problem.add_goal(on(block_3, block_2))

```

#### PDDL domain

```lisp
(define (domain hierarchical_blocks_world_object_as_root_domain)
 (:requirements :strips :typing)
 (:types
    object_ - object
    entity - object_
    location - entity
    movable unmovable - location
    tablespace - unmovable
    block - movable
 )
 (:predicates 
             (clear ?space - location)
             (on ?object - movable ?space - location)
 )
 (:action move
  :parameters ( ?item - movable ?l_from - location ?l_to - location)
  :precondition (and (clear ?item) (clear ?l_to) (on ?item ?l_from))
  :effect (and (clear ?l_from) (not (on ?item ?l_from)) (not (clear ?l_to)) (on ?item ?l_to)))
)
```

### hierarchical_blocks_world_with_object

This example defines `hierarchical_blocks_world_with_object` with 2 fluent(s), 1 action(s), and 6 object(s). Primary action(s): move. Goal summary: on(block_1, ts_3); on(block_2, block_1); .... Special features: classical planning only.

#### unified-planning

```python
    # hierarchical blocks world with object
    Entity = UserType("Entity", None)  # None can be avoided
    object = UserType("object", Entity)
    Unmovable = UserType("Unmovable", object)
    TableSpace = UserType("TableSpace", Unmovable)
    Movable = UserType("Movable", object)
    Block = UserType("Block", Movable)
    clear = Fluent("clear", BoolType(), space=object)
    on = Fluent("on", BoolType(), object=Movable, space=object)

    move = InstantaneousAction("move", item=Movable, l_from=object, l_to=object)
    item = move.parameter("item")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(clear(item))
    move.add_precondition(clear(l_to))
    move.add_precondition(on(item, l_from))
    move.add_effect(clear(l_from), True)
    move.add_effect(on(item, l_from), False)
    move.add_effect(clear(l_to), False)
    move.add_effect(on(item, l_to), True)

    problem = Problem("hierarchical_blocks_world_with_object")
    problem.add_fluent(clear, default_initial_value=False)
    problem.add_fluent(on, default_initial_value=False)
    problem.add_action(move)
    ts_1 = Object("ts_1", TableSpace)
    ts_2 = Object("ts_2", TableSpace)
    ts_3 = Object("ts_3", TableSpace)
    problem.add_objects([ts_1, ts_2, ts_3])
    block_1 = Object("block_1", Block)
    block_2 = Object("block_2", Block)
    block_3 = Object("block_3", Block)
    problem.add_objects([block_1, block_2, block_3])

    # The blocks are all on ts_1, in order block_3 under block_1 under block_2
    problem.set_initial_value(clear(ts_2), True)
    problem.set_initial_value(clear(ts_3), True)
    problem.set_initial_value(clear(block_2), True)
    problem.set_initial_value(on(block_3, ts_1), True)
    problem.set_initial_value(on(block_1, block_3), True)
    problem.set_initial_value(on(block_2, block_1), True)

    # We want them on ts_3 in order block_3 on block_2 on block_1
    problem.add_goal(on(block_1, ts_3))
    problem.add_goal(on(block_2, block_1))
    problem.add_goal(on(block_3, block_2))

```

#### PDDL domain

```lisp
(define (domain hierarchical_blocks_world_with_object_domain)
 (:requirements :strips :typing)
 (:types
    entity - object
    object_ - entity
    movable unmovable - object_
    tablespace - unmovable
    block - movable
 )
 (:predicates 
             (clear ?space - object_)
             (on ?object - movable ?space - object_)
 )
 (:action move
  :parameters ( ?item - movable ?l_from - object_ ?l_to - object_)
  :precondition (and (clear ?item) (clear ?l_to) (on ?item ?l_from))
  :effect (and (clear ?l_from) (not (on ?item ?l_from)) (not (clear ?l_to)) (on ?item ?l_to)))
)
```

### travel_with_consumptions

This example defines `travel_with_consumptions` with 6 fluent(s), 1 action(s), and 5 object(s). Primary action(s): move. Goal summary: is_at(l5). Special features: integer fluents, 1 quality metric(s).

#### unified-planning

```python
    # travel with consumptions
    problem = Problem("travel_with_consumptions")

    Location = UserType("Location")

    is_at = Fluent("is_at", BoolType(), position=Location)
    is_connected = Fluent("is_connected", BoolType(), l_from=Location, l_to=Location)
    travel_time = Fluent("travel_time", IntType(0, 500), l_from=Location, l_to=Location)
    road_consumption_factor = Fluent("road_consumption_factor", IntType(5, 100), l_from=Location, l_to=Location)
    total_travel_time = Fluent("total_travel_time", IntType())
    total_fuel_consumption = Fluent("total_fuel_consumption", IntType())

    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_fluent(travel_time, default_initial_value=500)
    problem.add_fluent(road_consumption_factor, default_initial_value=100)
    problem.add_fluent(total_travel_time, default_initial_value=0)
    problem.add_fluent(total_fuel_consumption, default_initial_value=0)

    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(is_at(l_from))
    move.add_precondition(is_connected(l_from, l_to))
    move.add_effect(is_at(l_from), False)
    move.add_effect(is_at(l_to), True)
    move.add_increase_effect(total_travel_time, travel_time(l_from, l_to))
    move.add_increase_effect(
        total_fuel_consumption,
        travel_time(l_from, l_to) * road_consumption_factor(l_from, l_to),
    )
    problem.add_action(move)

    problem.add_quality_metric(
        up.model.metrics.MinimizeExpressionOnFinalState(2 * total_fuel_consumption + 50 * total_travel_time)
    )

    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    problem.add_objects([l1, l2, l3, l4, l5])

    problem.set_initial_value(is_at(l1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l1, l3), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.set_initial_value(is_connected(l3, l5), True)
    problem.set_initial_value(travel_time(l1, l2), 60)
    problem.set_initial_value(travel_time(l2, l3), 70)
    problem.set_initial_value(travel_time(l1, l3), 100)
    problem.set_initial_value(travel_time(l3, l4), 100)
    problem.set_initial_value(travel_time(l4, l5), 120)
    problem.set_initial_value(travel_time(l3, l5), 200)
    problem.set_initial_value(road_consumption_factor(l1, l2), 30)
    problem.set_initial_value(road_consumption_factor(l2, l3), 27)
    problem.set_initial_value(road_consumption_factor(l1, l3), 50)
    problem.set_initial_value(road_consumption_factor(l3, l4), 15)
    problem.set_initial_value(road_consumption_factor(l4, l5), 13)
    problem.set_initial_value(road_consumption_factor(l3, l5), 40)

    problem.add_goal(is_at(l5))

```

#### PDDL domain

```lisp
(define (domain travel_with_consumptions_domain)
 (:requirements :strips :typing :numeric-fluents)
 (:types location)
 (:predicates 
             (is_at ?position - location)
             (is_connected ?l_from - location ?l_to - location)
 )
 (:functions 
             (travel_time ?l_from - location ?l_to - location)
             (road_consumption_factor ?l_from - location ?l_to - location)
             (total_travel_time)
             (total_fuel_consumption)
 )
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and (is_at ?l_from) (is_connected ?l_from ?l_to))
  :effect (and (not (is_at ?l_from)) (is_at ?l_to) (increase (total_travel_time) (travel_time ?l_from ?l_to)) (increase (total_fuel_consumption) (* (road_consumption_factor ?l_from ?l_to) (travel_time ?l_from ?l_to)))))
)
```

### matchcellar_static_duration

This example defines `matchcellar_static_duration` with 6 fluent(s), 2 action(s), and 6 object(s). Primary action(s): light_match, mend_fuse. Goal summary: fuse_mended(f1); fuse_mended(f2); .... Special features: continuous time.

#### unified-planning

```python
    # matchcellar with static duration
    Match = UserType("Match")
    Fuse = UserType("Fuse")
    handfree = Fluent("handfree")
    light = Fluent("light")
    match_durability = Fluent("match_durability", RealType(), match=Match)
    fuse_difficulty = Fluent("fuse_difficulty", RealType(), fuse=Fuse)
    match_used = Fluent("match_used", BoolType(), match=Match)
    fuse_mended = Fluent("fuse_mended", BoolType(), fuse=Fuse)
    light_match = DurativeAction("light_match", m=Match)
    m = light_match.parameter("m")
    light_match.set_fixed_duration(match_durability(m))
    light_match.add_condition(StartTiming(), Not(match_used(m)))
    light_match.add_effect(StartTiming(), match_used(m), True)
    light_match.add_effect(StartTiming(), light, True)
    light_match.add_effect(EndTiming(), light, False)
    mend_fuse = DurativeAction("mend_fuse", f=Fuse)
    f = mend_fuse.parameter("f")
    mend_fuse.set_fixed_duration(fuse_difficulty(f))
    mend_fuse.add_condition(StartTiming(), handfree)
    mend_fuse.add_condition(ClosedTimeInterval(StartTiming(), EndTiming()), light)
    mend_fuse.add_effect(StartTiming(), handfree, False)
    mend_fuse.add_effect(EndTiming(), fuse_mended(f), True)
    mend_fuse.add_effect(EndTiming(), handfree, True)
    f1 = Object("f1", Fuse)
    f2 = Object("f2", Fuse)
    f3 = Object("f3", Fuse)
    m1 = Object("m1", Match)
    m2 = Object("m2", Match)
    m3 = Object("m3", Match)
    problem = Problem("matchcellar_static_duration")
    problem.add_fluent(handfree)
    problem.add_fluent(light)
    problem.add_fluent(match_durability)
    problem.add_fluent(fuse_difficulty)
    problem.add_fluent(match_used, default_initial_value=False)
    problem.add_fluent(fuse_mended, default_initial_value=False)
    problem.add_action(light_match)
    problem.add_action(mend_fuse)
    problem.add_object(f1)
    problem.add_object(f2)
    problem.add_object(f3)
    problem.add_object(m1)
    problem.add_object(m2)
    problem.add_object(m3)
    problem.set_initial_value(light, False)
    problem.set_initial_value(handfree, True)
    problem.set_initial_value(match_durability(m1), 2)
    problem.set_initial_value(match_durability(m2), 3)
    problem.set_initial_value(match_durability(m3), 4)
    problem.set_initial_value(fuse_difficulty(f1), 1)
    problem.set_initial_value(fuse_difficulty(f2), 2)
    problem.set_initial_value(fuse_difficulty(f3), 3)
    problem.add_goal(fuse_mended(f1))
    problem.add_goal(fuse_mended(f2))
    problem.add_goal(fuse_mended(f3))
```

#### PDDL domain

```lisp
(define (domain matchcellar_static_duration_domain)
 (:requirements :strips :typing :negative-preconditions :durative-actions)
 (:types match fuse)
 (:predicates 
             (handfree)
             (light)
             (match_used ?match - match)
             (fuse_mended ?fuse - fuse)
 )
 (:functions 
             (match_durability ?match - match)
             (fuse_difficulty ?fuse - fuse)
 )
 (:durative-action light_match
  :parameters ( ?m - match)
  :duration (= ?duration (match_durability ?m))
  :condition (and 
                 (at start (not (match_used ?m)))
             )
  :effect (and
              (at start (match_used ?m))
              (at start (light))
              (at end (not (light)))
          )
 )
 (:durative-action mend_fuse
  :parameters ( ?f - fuse)
  :duration (= ?duration (fuse_difficulty ?f))
  :condition (and 
                 (at start (handfree))
                 (at start (light))(over all (light))(at end (light))
             )
  :effect (and
              (at start (not (handfree)))
              (at end (fuse_mended ?f))
              (at end (handfree))
          )
 )
)
```

### locations_connected_visited_oversubscription

This example defines `locations_connected_visited_oversubscription` with 3 fluent(s), 1 action(s), and 5 object(s). Primary action(s): move. Goal summary: is_at(l5). Special features: universal conditions, 1 quality metric(s).

#### unified-planning

```python
    # locations connected visited oversubscription
    Location = UserType("Location")
    is_at = Fluent("is_at", BoolType(), position=Location)
    is_connected = Fluent("is_connected", BoolType(), location_1=Location, location_2=Location)
    visited = Fluent("visited", BoolType(), location=Location)
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(is_at(l_from))
    move.add_precondition(Not(is_at(l_to)))
    move.add_precondition(is_connected(l_from, l_to))
    move.add_effect(is_at(l_from), False)
    move.add_effect(is_at(l_to), True)
    move.add_effect(visited(l_to), True)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    problem = Problem("locations_connected_visited_oversubscription")
    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(visited, default_initial_value=False)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(l3)
    problem.add_object(l4)
    problem.add_object(l5)
    problem.set_initial_value(is_at(l1), True)
    problem.set_initial_value(visited(l1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l1, l3), True)
    problem.set_initial_value(is_connected(l1, l5), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l2, l5), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.add_goal(is_at(l5))
    loc_var = Variable("loc_var", Location)
    problem.add_quality_metric(
        Oversubscription(
            {
                visited(l2): 9,
                visited(l2) | visited(l3): 5,
                Forall(visited(loc_var) | loc_var.Equals(l2), loc_var) & visited(l2).Not(): 10,
            }
        )
    )

```

#### PDDL domain

```lisp
(define (domain locations_connected_visited_oversubscription_domain)
 (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :equality :universal-preconditions)
 (:types location)
 (:predicates 
             (is_at ?position - location)
             (visited ?location - location)
             (is_connected ?location_1 - location ?location_2 - location)
 )
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and (not (= ?l_from ?l_to)) (is_at ?l_from) (not (is_at ?l_to)) (is_connected ?l_from ?l_to))
  :effect (and (not (is_at ?l_from)) (is_at ?l_to) (visited ?l_to)))
)
```

### locations_connected_cost_minimize

This example defines `locations_connected_cost_minimize` with 3 fluent(s), 1 action(s), and 5 object(s). Primary action(s): move. Goal summary: is_at(l5). Special features: action costs, 1 quality metric(s).

#### unified-planning

```python
    # locations connected cost minimize
    Location = UserType("Location")
    is_at = Fluent("is_at", BoolType(), position=Location)
    is_connected = Fluent("is_connected", BoolType(), location_1=Location, location_2=Location)
    distance = Fluent("distance", RealType(), location_1=Location, location_2=Location)
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(is_at(l_from))
    move.add_precondition(Not(is_at(l_to)))
    move.add_precondition(Or(is_connected(l_from, l_to), is_connected(l_to, l_from)))
    move.add_effect(is_at(l_from), False)
    move.add_effect(is_at(l_to), True)
    move_cost = distance(l_from, l_to)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    problem = Problem("locations_connected_cost_minimize")
    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_fluent(distance, default_initial_value=100)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(l3)
    problem.add_object(l4)
    problem.add_object(l5)
    problem.set_initial_value(is_at(l1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l1, l3), True)
    problem.set_initial_value(is_connected(l1, l5), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l2, l5), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.set_initial_value(distance(l1, l2), 4)
    problem.set_initial_value(distance(l1, l3), 8)
    problem.set_initial_value(distance(l1, l5), 11)
    problem.set_initial_value(distance(l2, l3), 5)
    problem.set_initial_value(distance(l2, l5), 8)
    problem.set_initial_value(distance(l3, l4), 1)
    problem.set_initial_value(distance(l4, l5), 1)

    problem.set_initial_value(distance(l2, l1), 4)
    problem.set_initial_value(distance(l3, l1), 8)
    problem.set_initial_value(distance(l5, l1), 11)
    problem.set_initial_value(distance(l3, l2), 5)
    problem.set_initial_value(distance(l5, l2), 8)
    problem.set_initial_value(distance(l4, l3), 1)
    problem.set_initial_value(distance(l5, l4), 1)
    problem.add_goal(is_at(l5))
    problem.add_quality_metric(MinimizeActionCosts({move: move_cost}))

```

#### PDDL domain

```lisp
(define (domain locations_connected_cost_minimize_domain)
 (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :equality :action-costs)
 (:types location)
 (:predicates 
             (is_at ?position - location)
             (is_connected ?location_1 - location ?location_2 - location)
 )
 (:functions 
             (distance ?location_1 - location ?location_2 - location)
             (total-cost)
 )
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and (not (= ?l_from ?l_to)) (is_at ?l_from) (not (is_at ?l_to)) (or (is_connected ?l_from ?l_to) (is_connected ?l_to ?l_from)))
  :effect (and (not (is_at ?l_from)) (is_at ?l_to) (increase (total-cost) (distance ?l_from ?l_to))))
)
```

### robot_conditional_effects

This example defines `robot_conditional_effects` with 3 fluent(s), 1 action(s), and 2 object(s). Primary action(s): move. Goal summary: robot_at(l2); (battery_charge == 90). Special features: continuous time, conditional effects, real fluents.

#### unified-planning

```python
    # robot_conditional_effects
    Location = UserType("Location")
    connected = Fluent("connected", BoolType(), l_from=Location, l_to=Location)
    robot_at = Fluent("robot_at", BoolType(), position=Location)
    battery_charge = Fluent("battery_charge", RealType(0, 100))
    move_cond = DurativeAction("move", l_from=Location, l_to=Location)
    l_from = move_cond.parameter("l_from")
    l_to = move_cond.parameter("l_to")
    move_cond.set_fixed_duration(10)
    move_cond.add_condition(StartTiming(), connected(l_from, l_to))
    move_cond.add_condition(StartTiming(), robot_at(l_from))
    move_cond.add_condition(StartTiming(), GE(battery_charge, 10))
    move_cond.add_effect(StartTiming(), robot_at(l_from), False)
    move_cond.add_effect(EndTiming(), robot_at(l_to), True, GE(battery_charge, 10))
    move_cond.add_decrease_continuous_effect(
        ClosedTimeInterval(StartTiming(), EndTiming()),
        battery_charge,
        1,
    )
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot_conditional_effects")
    problem.add_fluent(robot_at, default_initial_value=False)
    problem.add_fluent(connected, default_initial_value=False)
    problem.add_fluent(battery_charge, default_initial_value=100)
    problem.add_action(move_cond)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(connected(l1, l2), True)
    problem.set_initial_value(robot_at(l1), True)
    problem.add_goal(robot_at(l2))
    problem.add_goal(Equals(battery_charge, 90))
```

#### PDDL domain

```lisp
(define (domain robot_conditional_effects_domain)
 (:requirements :strips :typing :equality :numeric-fluents :conditional-effects :durative-actions :continuous-effects)
 (:types location)
 (:predicates 
             (robot_at ?position - location)
             (connected ?l_from - location ?l_to - location)
 )
 (:functions 
             (battery_charge)
 )
 (:durative-action move
  :parameters ( ?l_from - location ?l_to - location)
  :duration (= ?duration 10)
  :condition (and 
                 (at start (connected ?l_from ?l_to))
                 (at start (robot_at ?l_from))
                 (at start (<= 10 (battery_charge)))
             )
  :effect (and
              (at start (not (robot_at ?l_from)))
              (when (at end (<= 10 (battery_charge))) (at end (robot_at ?l_to)))
 (decrease (battery_charge) (* #t 1))
          )
 )
)
```

### robot_non_linear_continuous_1

This example defines `robot_non_linear_continuous_1` with 4 fluent(s), 1 action(s), and 2 object(s). Primary action(s): move. Goal summary: robot_at(l2); (battery_charge == 95). Special features: continuous time, real fluents.

#### unified-planning

```python
    # robot_non_linear_continuous_1
    Location = UserType("Location")
    connected = Fluent("connected", BoolType(), l_from=Location, l_to=Location)
    robot_at = Fluent("robot_at", BoolType(), position=Location)
    battery_charge = Fluent("battery_charge", RealType(0, 100))
    derivative = Fluent("derivative", RealType())
    move_non_lin = DurativeAction("move", l_from=Location, l_to=Location)
    l_from = move_non_lin.parameter("l_from")
    l_to = move_non_lin.parameter("l_to")
    move_non_lin.set_fixed_duration(10)
    move_non_lin.add_condition(StartTiming(), connected(l_from, l_to))
    move_non_lin.add_condition(StartTiming(), robot_at(l_from))
    move_non_lin.add_effect(StartTiming(), robot_at(l_from), False)
    move_non_lin.add_effect(EndTiming(), robot_at(l_to), True)
    move_non_lin.add_decrease_continuous_effect(
        ClosedTimeInterval(StartTiming(), EndTiming()), battery_charge, derivative
    )
    move_non_lin.add_increase_continuous_effect(
        ClosedTimeInterval(StartTiming(), EndTiming()), derivative, Fraction(1, 10)
    )
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot_non_linear_continuous_1")
    problem.add_fluent(robot_at, default_initial_value=False)
    problem.add_fluent(connected, default_initial_value=False)
    problem.add_fluent(battery_charge, default_initial_value=100)
    problem.add_fluent(derivative, default_initial_value=0)
    problem.add_action(move_non_lin)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(connected(l1, l2), True)
    problem.set_initial_value(robot_at(l1), True)
    problem.add_goal(robot_at(l2))
    problem.add_goal(Equals(battery_charge, 95))
```

#### PDDL domain

```lisp
(define (domain robot_non_linear_continuous_1_domain)
 (:requirements :strips :typing :equality :numeric-fluents :durative-actions :continuous-effects)
 (:types location)
 (:predicates 
             (robot_at ?position - location)
             (connected ?l_from - location ?l_to - location)
 )
 (:functions 
             (battery_charge)
             (derivative)
 )
 (:durative-action move
  :parameters ( ?l_from - location ?l_to - location)
  :duration (= ?duration 10)
  :condition (and 
                 (at start (connected ?l_from ?l_to))
                 (at start (robot_at ?l_from))
             )
  :effect (and
              (at start (not (robot_at ?l_from)))
              (at end (robot_at ?l_to))
 (decrease (battery_charge) (* #t (derivative)))
 (increase (derivative) (* #t 0.1))
          )
 )
)
```
## processes

### Problems

- [1d_movement](#1d_movement)
- [boiling_water](#boiling_water)

### 1d_movement

This example defines `1d_movement` with 2 fluent(s), 1 action(s), and 0 object(s). Primary action(s): turn_on. Goal summary: (10 <= d). Special features: processes, events, real fluents, 1 process(es) and 1 event(s).

#### unified-planning

```python
    on = Fluent("on")
    d = Fluent("d", RealType())

    a = InstantaneousAction("turn_on")
    a.add_precondition(Not(on))
    a.add_effect(on, True)

    evt = Event("turn_off_automatically")
    evt.add_precondition(GE(d, 200))
    evt.add_effect(on, False)

    b = Process("moving")
    b.add_precondition(on)
    b.add_increase_continuous_effect(d, 1)

    problem = Problem("1d_Movement")
    problem.add_fluent(on)
    problem.add_fluent(d)
    problem.add_action(a)
    problem.add_process(b)
    problem.add_event(evt)
    problem.set_initial_value(on, False)
    problem.set_initial_value(d, 0)
    problem.add_goal(GE(d, 10))

    z = Fluent("z", BoolType())
    pr = Process("Name")
    pr.add_precondition(z)
```

#### PDDL domain

```lisp
(define (domain p_1d_movement_domain)
 (:requirements :strips :negative-preconditions :numeric-fluents :continuous-effects :time)
 (:predicates 
             (on)
 )
 (:functions 
             (d)
 )
 (:action turn_on
  :parameters ()
  :precondition (and (not (on)))
  :effect (and (on)))
 (:process moving
  :parameters ()
  :precondition (and (on))
  :effect (and (increase (d) (* #t 1 ))))
 (:event turn_off_automatically
  :parameters ()
  :precondition (and (<= 200 (d)))
  :effect (and (not (on))))
)
```

### boiling_water

This example defines `boiling_water` with 4 fluent(s), 1 action(s), and 0 object(s). Primary action(s): turn_on_boiler. Goal summary: ((not boiler_on) and (chimney_vent_open and (water_level <= 2))). Special features: processes, events, real fluents, 2 process(es) and 2 event(s).

#### unified-planning

```python
    problem = Problem("boiling_water")
    boiler_on = Fluent("boiler_on")
    temperature = Fluent("temperature", RealType())
    water_level = Fluent("water_level", RealType())
    chimney_vent_open = Fluent("chimney_vent_open")

    turn_on_boiler = InstantaneousAction("turn_on_boiler")
    turn_on_boiler.add_precondition(Not(boiler_on))
    turn_on_boiler.add_effect(boiler_on, True)

    water_heating = Process("water_heating")
    water_heating.add_precondition(And(boiler_on, LE(temperature, 100)))
    water_heating.add_increase_continuous_effect(temperature, 1)

    water_boiling = Process("water_boiling")
    water_boiling.add_precondition(And(boiler_on, GE(temperature, 100)))
    water_boiling.add_decrease_continuous_effect(water_level, 1)

    open_chimney_vent_auto = Event("open_chimney_vent_auto")
    open_chimney_vent_auto.add_precondition(And(Not(chimney_vent_open), GE(temperature, 100)))
    open_chimney_vent_auto.add_effect(chimney_vent_open, True)

    turn_off_boiler_auto = Event("turn_off_boiler_auto")
    turn_off_boiler_auto.add_precondition(And(LE(water_level, 0), boiler_on))
    turn_off_boiler_auto.add_effect(boiler_on, False)

    problem.add_fluent(boiler_on)
    problem.set_initial_value(boiler_on, False)
    problem.add_fluent(chimney_vent_open)
    problem.set_initial_value(chimney_vent_open, False)
    problem.add_fluent(temperature)
    problem.set_initial_value(temperature, 20)
    problem.add_fluent(water_level)
    problem.set_initial_value(water_level, 10)
    problem.add_action(turn_on_boiler)
    problem.add_process(water_heating)
    problem.add_process(water_boiling)
    problem.add_event(open_chimney_vent_auto)
    problem.add_event(turn_off_boiler_auto)
    problem.add_goal(And(Not(boiler_on), And(chimney_vent_open, LE(water_level, 2))))

```

#### PDDL domain

```lisp
(define (domain boiling_water_domain)
 (:requirements :strips :negative-preconditions :numeric-fluents :continuous-effects :time)
 (:predicates 
             (boiler_on)
             (chimney_vent_open)
 )
 (:functions 
             (temperature)
             (water_level)
 )
 (:action turn_on_boiler
  :parameters ()
  :precondition (and (not (boiler_on)))
  :effect (and (boiler_on)))
 (:process water_heating
  :parameters ()
  :precondition (and (boiler_on) (<= (temperature) 100))
  :effect (and (increase (temperature) (* #t 1 ))))
 (:process water_boiling
  :parameters ()
  :precondition (and (boiler_on) (<= 100 (temperature)))
  :effect (and (decrease (water_level) (* #t 1 ))))
 (:event open_chimney_vent_auto
  :parameters ()
  :precondition (and (not (chimney_vent_open)) (<= 100 (temperature)))
  :effect (and (chimney_vent_open)))
 (:event turn_off_boiler_auto
  :parameters ()
  :precondition (and (<= (water_level) 0) (boiler_on))
  :effect (and (not (boiler_on))))
)
```
## multi_agent

### Problems

- [ma_basic](#ma_basic)
- [ma_loader](#ma_loader)
- [ma_buttons](#ma_buttons)

### ma_basic

This multi-agent example defines `ma-basic` with 1 agent(s) (robot). The model exposes 1 shared environment fluent(s) and exports factored MA-PDDL per agent.

#### unified-planning

```python
    # basic multi agent
    problem = MultiAgentProblem("ma-basic")

    Location = UserType("Location")

    is_connected = Fluent("is_connected", BoolType(), l1=Location, l2=Location)
    problem.ma_environment.add_fluent(is_connected, default_initial_value=False)

    r = Agent("robot", problem)
    pos = Fluent("pos", position=Location)
    r.add_fluent(pos, default_initial_value=False)
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(pos(l_from))
    move.add_precondition(is_connected(l_from, l_to))
    move.add_effect(pos(l_to), True)
    move.add_effect(pos(l_from), False)
    r.add_action(move)
    problem.add_agent(r)

    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem.add_objects([l1, l2])

    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(Dot(r, pos(l1)), True)
    problem.add_goal(Dot(r, pos(l2)))

```

##### MA-PDDL domain (robot)

```lisp
(define (domain ma-basic_domain)
 (:requirements :multi-agent :factored-privacy :typing)
 (:types location ag - object
    robot_type - ag
 )
 (:predicates
  (is_connected ?l1 - location ?l2 - location)
  (:private
   (a_pos ?agent - ag ?position - location)))
 (:action move
  :parameters ( ?robot - robot_type ?l_from - location ?l_to - location)
  :precondition (and 
   (a_pos  ?robot ?l_from)
   (is_connected ?l_from ?l_to)
  )
  :effect (and
 (a_pos  ?robot ?l_to) (not (a_pos  ?robot ?l_from))))
)
```

### ma_loader

This multi-agent example defines `ma-loader` with 2 agent(s) (robot1, robot2). The model exposes 2 shared environment fluent(s) and exports factored MA-PDDL per agent.

#### unified-planning

```python
    # Loader multi agent
    problem = MultiAgentProblem("ma-loader")

    Location = UserType("Location")

    is_connected = Fluent("is_connected", BoolType(), l1=Location, l2=Location)
    cargo_at = Fluent("cargo_at", BoolType(), position=Location)
    problem.ma_environment.add_fluent(is_connected, default_initial_value=False)
    problem.ma_environment.add_fluent(cargo_at, default_initial_value=False)

    robot1 = Agent("robot1", problem)
    robot2 = Agent("robot2", problem)
    pos = Fluent("pos", position=Location)

    cargo_mounted = Fluent("cargo_mounted")
    robot1.add_fluent(pos, default_initial_value=False)
    robot1.add_fluent(cargo_mounted)
    robot2.add_fluent(pos, default_initial_value=False)
    robot2.add_fluent(cargo_mounted)

    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(pos(l_from))
    move.add_precondition(is_connected(l_from, l_to))
    move.add_effect(pos(l_to), True)
    move.add_effect(pos(l_from), False)

    load = InstantaneousAction("load", loc=Location)
    loc = load.parameter("loc")
    load.add_precondition(cargo_at(loc))
    load.add_precondition(pos(loc))
    load.add_precondition(Not(cargo_mounted))
    load.add_effect(cargo_at(loc), False)
    load.add_effect(cargo_mounted, True)

    unload = InstantaneousAction("unload", loc=Location)
    loc = unload.parameter("loc")
    unload.add_precondition(Not(cargo_at(loc)))
    unload.add_precondition(pos(loc))
    unload.add_precondition(cargo_mounted)
    unload.add_effect(cargo_at(loc), True)
    unload.add_effect(cargo_mounted, False)

    robot1.add_action(move)
    robot2.add_action(move)
    robot1.add_action(load)
    robot2.add_action(load)
    robot1.add_action(unload)
    robot2.add_action(unload)
    problem.add_agent(robot1)
    problem.add_agent(robot2)

    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    problem.add_objects([l1, l2, l3])

    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l1), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(Dot(robot1, pos(l2)), True)
    problem.set_initial_value(Dot(robot2, pos(l2)), True)
    problem.set_initial_value(cargo_at(l1), True)
    problem.set_initial_value(cargo_at(l2), False)
    problem.set_initial_value(cargo_at(l3), False)
    problem.set_initial_value(Dot(robot1, cargo_mounted), False)
    problem.set_initial_value(Dot(robot2, cargo_mounted), False)

    problem.add_goal(cargo_at(l3))

```

##### MA-PDDL domain (robot1)

```lisp
(define (domain ma-loader_domain)
 (:requirements :multi-agent :factored-privacy :typing :negative-preconditions)
 (:types location ag - object
    robot1_type robot2_type - ag
 )
 (:predicates
  (is_connected ?l1 - location ?l2 - location)
  (cargo_at ?position - location)
  (:private
   (a_pos ?agent - ag ?position - location)
   (a_cargo_mounted ?agent - ag)))
 (:action move
  :parameters ( ?robot1 - robot1_type ?l_from - location ?l_to - location)
  :precondition (and 
   (a_pos  ?robot1 ?l_from)
   (is_connected ?l_from ?l_to)
  )
  :effect (and
 (a_pos  ?robot1 ?l_to) (not (a_pos  ?robot1 ?l_from))))
 (:action load
  :parameters ( ?robot1 - robot1_type ?loc - location)
  :precondition (and 
   (cargo_at ?loc)
   (a_pos  ?robot1 ?loc)
   (not (a_cargo_mounted  ?robot1))
  )
  :effect (and
 (not (cargo_at ?loc)) (a_cargo_mounted  ?robot1)))
 (:action unload
  :parameters ( ?robot1 - robot1_type ?loc - location)
  :precondition (and 
   (not (cargo_at ?loc))
   (a_pos  ?robot1 ?loc)
   (a_cargo_mounted  ?robot1)
  )
  :effect (and
 (cargo_at ?loc) (not (a_cargo_mounted  ?robot1))))
)
```

##### MA-PDDL domain (robot2)

```lisp
(define (domain ma-loader_domain)
 (:requirements :multi-agent :factored-privacy :typing :negative-preconditions)
 (:types location ag - object
    robot1_type robot2_type - ag
 )
 (:predicates
  (is_connected ?l1 - location ?l2 - location)
  (cargo_at ?position - location)
  (:private
   (a_pos ?agent - ag ?position - location)
   (a_cargo_mounted ?agent - ag)))
 (:action move
  :parameters ( ?robot2 - robot2_type ?l_from - location ?l_to - location)
  :precondition (and 
   (a_pos  ?robot2 ?l_from)
   (is_connected ?l_from ?l_to)
  )
  :effect (and
 (a_pos  ?robot2 ?l_to) (not (a_pos  ?robot2 ?l_from))))
 (:action load
  :parameters ( ?robot2 - robot2_type ?loc - location)
  :precondition (and 
   (cargo_at ?loc)
   (a_pos  ?robot2 ?loc)
   (not (a_cargo_mounted  ?robot2))
  )
  :effect (and
 (not (cargo_at ?loc)) (a_cargo_mounted  ?robot2)))
 (:action unload
  :parameters ( ?robot2 - robot2_type ?loc - location)
  :precondition (and 
   (not (cargo_at ?loc))
   (a_pos  ?robot2 ?loc)
   (a_cargo_mounted  ?robot2)
  )
  :effect (and
 (cargo_at ?loc) (not (a_cargo_mounted  ?robot2))))
)
```

### ma_buttons

This multi-agent example defines `ma_buttons` with 3 agent(s) (a1, a2, a3). The model exposes 6 shared environment fluent(s) and exports factored MA-PDDL per agent.

#### unified-planning

```python
    # TYPEs
    Location = UserType("Location")
    button = UserType("button")
    problem = MultiAgentProblem("ma_bottons")

    reedButton = Object("reedButton", button)
    reedButton1 = Object("reedButton1", button)
    reedButton2 = Object("reedButton2", button)
    greenButton = Object("greenButton", button)
    yellowButton = Object("yellowButton", button)

    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    l6 = Object("l6", Location)
    l7 = Object("l7", Location)
    l8 = Object("l8", Location)
    problem.add_objects([l1, l2, l3, l4, l5, l6, l7, l8])
    problem.add_object(reedButton)
    problem.add_object(reedButton1)
    problem.add_object(reedButton2)
    problem.add_object(greenButton)
    problem.add_object(yellowButton)

    # FLUENTS
    activeButton = Fluent("activeButton", button=button)
    pressButton = Fluent(
        "pressButton",
        BoolType(),
        button=button,
        position=Location,
        connect_from=Location,
        connect_to=Location,
    )
    pressButton_contemp = Fluent(
        "pressButton_contemp",
        BoolType(),
        button=button,
        position=Location,
        connect_from=Location,
        connect_to=Location,
    )
    at_gB = Fluent(
        "at_gB",
        BoolType(),
        postion=Location,
        connect_from=Location,
        connect_to=Location,
    )
    at_rB = Fluent(
        "at_rB",
        BoolType(),
        postion=Location,
        connect_from=Location,
        connect_to=Location,
    )

    # AGENTs
    a1 = Agent("a1", problem)
    a2 = Agent("a2", problem)
    a3 = Agent("a3", problem)

    is_connected = Fluent("is_connected", BoolType(), l1=Location, l2=Location)
    problem.ma_environment.add_fluent(is_connected, default_initial_value=False)
    pos = Fluent("pos", position=Location)
    a1.add_public_fluent(pos, default_initial_value=False)
    a2.add_public_fluent(pos, default_initial_value=False)
    a3.add_public_fluent(pos, default_initial_value=False)

    problem.ma_environment.add_fluent(activeButton, default_initial_value=False)
    problem.ma_environment.add_fluent(pressButton, default_initial_value=False)
    problem.ma_environment.add_fluent(pressButton_contemp, default_initial_value=False)
    problem.ma_environment.add_fluent(at_gB, default_initial_value=False)
    problem.ma_environment.add_fluent(at_rB, default_initial_value=False)

    # ACTIONS
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(pos(l_from))
    move.add_precondition(is_connected(l_from, l_to))
    move.add_effect(pos(l_to), True)
    move.add_effect(pos(l_from), False)

    push_button = InstantaneousAction(
        "push_button",
        butt=button,
        loc=Location,
        connect_from=Location,
        connect_to=Location,
    )  # , l_from=Location, l_to=Location)
    butt = push_button.parameter("butt")
    loc = push_button.parameter("loc")
    connect_from = push_button.parameter("connect_from")
    connect_to = push_button.parameter("connect_to")
    push_button.add_precondition(pos(loc))
    push_button.add_precondition(pressButton(butt, loc, connect_from, connect_to))
    push_button.add_precondition(Not(activeButton(butt)))
    push_button.add_effect(activeButton(butt), True)
    push_button.add_effect(is_connected(connect_from, connect_to), True)

    push_red_button1 = InstantaneousAction(
        "push_red_button1",
        butt=button,
        loc=Location,
        connect_from=Location,
        connect_to=Location,
    )
    loc = push_red_button1.parameter("loc")
    connect_from = push_red_button1.parameter("connect_from")
    connect_to = push_red_button1.parameter("connect_to")
    butt = push_red_button1.parameter("butt")
    push_red_button1.add_precondition(Dot(a3, pos(loc)))
    push_red_button1.add_precondition(Dot(a2, pos(loc)))
    push_red_button1.add_precondition(pressButton_contemp(butt, loc, connect_from, connect_to))
    push_red_button1.add_effect(activeButton(reedButton2), True, Not(activeButton(reedButton2)))

    push_red_button2 = InstantaneousAction(
        "push_red_button2",
        butt=button,
        loc=Location,
        connect_from=Location,
        connect_to=Location,
    )
    loc = push_red_button2.parameter("loc")
    connect_from = push_red_button2.parameter("connect_from")
    connect_to = push_red_button2.parameter("connect_to")
    butt = push_red_button2.parameter("butt")
    push_red_button2.add_precondition(Dot(a3, pos(loc)))
    push_red_button2.add_precondition(Dot(a2, pos(loc)))
    push_red_button2.add_precondition(pressButton_contemp(butt, loc, connect_from, connect_to))
    push_red_button2.add_effect(activeButton(reedButton1), True, Not(activeButton(reedButton1)))

    unpush_push_button = InstantaneousAction(
        "unpush_push_button",
        butt=button,
        loc=Location,
        connect_from=Location,
        connect_to=Location,
    )  # , l_from=Location, l_to=Location)
    loc = unpush_push_button.parameter("loc")
    connect_from = unpush_push_button.parameter("connect_from")
    connect_to = unpush_push_button.parameter("connect_to")
    butt = unpush_push_button.parameter("butt")
    unpush_push_button.add_precondition(Dot(a3, pos(loc)))
    unpush_push_button.add_precondition(Dot(a2, pos(loc)))
    unpush_push_button.add_precondition(activeButton(reedButton1))
    unpush_push_button.add_precondition(activeButton(reedButton2))
    unpush_push_button.add_precondition(pressButton_contemp(butt, loc, connect_from, connect_to))
    unpush_push_button.add_effect(
        is_connected(connect_from, connect_to),
        True,
        And(activeButton(reedButton1), activeButton(reedButton2)),
    )

    a1.add_action(move)
    a1.add_action(push_button)

    a2.add_action(move)
    a2.add_action(push_button)
    a2.add_action(unpush_push_button)
    a2.add_action(push_red_button1)

    a3.add_action(move)
    a3.add_action(push_button)
    a3.add_action(unpush_push_button)
    a3.add_action(push_red_button2)

    problem.add_agent(a1)
    problem.add_agent(a2)
    problem.add_agent(a3)

    # INITIAL VALUEs
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l5, l6), True)
    problem.set_initial_value(activeButton(reedButton), False)
    problem.set_initial_value(activeButton(reedButton1), False)
    problem.set_initial_value(activeButton(reedButton2), False)

    problem.set_initial_value(Dot(a1, pos(l1)), True)
    problem.set_initial_value(Dot(a2, pos(l4)), True)
    problem.set_initial_value(Dot(a3, pos(l7)), True)

    problem.set_initial_value(pressButton(yellowButton, l2, l4, l5), True)
    problem.set_initial_value(pressButton(greenButton, l5, l7, l6), True)
    problem.set_initial_value(pressButton_contemp(reedButton, l6, l2, l3), True)

    # GOALs
    problem.add_goal(Dot(a1, pos(l3)))
    problem.add_goal(Dot(a2, pos(l6)))
    problem.add_goal(Dot(a3, pos(l6)))

```

##### MA-PDDL domain (a1)

```lisp
(define (domain ma_bottons_domain)
 (:requirements :multi-agent :factored-privacy :typing :negative-preconditions :conditional-effects)
 (:types location button ag - object
    a1_type a2_type a3_type - ag
 )
 (:predicates
  (is_connected ?l1 - location ?l2 - location)
  (activebutton ?button - button)
  (pressbutton ?button - button ?position - location ?connect_from - location ?connect_to - location)
  (pressbutton_contemp ?button - button ?position - location ?connect_from - location ?connect_to - location)
  (at_gb ?postion - location ?connect_from - location ?connect_to - location)
  (at_rb ?postion - location ?connect_from - location ?connect_to - location)
  (a_pos ?agent - ag ?position - location)
)
 (:action move
  :parameters ( ?a1 - a1_type ?l_from - location ?l_to - location)
  :precondition (and 
   (a_pos  ?a1 ?l_from)
   (is_connected ?l_from ?l_to)
  )
  :effect (and
 (a_pos  ?a1 ?l_to) (not (a_pos  ?a1 ?l_from))))
 (:action push_button
  :parameters ( ?a1 - a1_type ?butt - button ?loc - location ?connect_from - location ?connect_to - location)
  :precondition (and 
   (a_pos  ?a1 ?loc)
   (pressbutton ?butt ?loc ?connect_from ?connect_to)
   (not (activebutton ?butt))
  )
  :effect (and
 (activebutton ?butt) (is_connected ?connect_from ?connect_to)))
)
```

##### MA-PDDL domain (a2)

```lisp
(define (domain ma_bottons_domain)
 (:requirements :multi-agent :factored-privacy :typing :negative-preconditions :conditional-effects)
 (:types location button ag - object
    a1_type a2_type a3_type - ag
 )
 (:constants
   reedbutton2 reedbutton1 - button
   a3 - a3_type
   a2 - a2_type
 )
 (:predicates
  (is_connected ?l1 - location ?l2 - location)
  (activebutton ?button - button)
  (pressbutton ?button - button ?position - location ?connect_from - location ?connect_to - location)
  (pressbutton_contemp ?button - button ?position - location ?connect_from - location ?connect_to - location)
  (at_gb ?postion - location ?connect_from - location ?connect_to - location)
  (at_rb ?postion - location ?connect_from - location ?connect_to - location)
  (a_pos ?agent - ag ?position - location)
)
 (:action move
  :parameters ( ?a2 - a2_type ?l_from - location ?l_to - location)
  :precondition (and 
   (a_pos  ?a2 ?l_from)
   (is_connected ?l_from ?l_to)
  )
  :effect (and
 (a_pos  ?a2 ?l_to) (not (a_pos  ?a2 ?l_from))))
 (:action push_button
  :parameters ( ?a2 - a2_type ?butt - button ?loc - location ?connect_from - location ?connect_to - location)
  :precondition (and 
   (a_pos  ?a2 ?loc)
   (pressbutton ?butt ?loc ?connect_from ?connect_to)
   (not (activebutton ?butt))
  )
  :effect (and
 (activebutton ?butt) (is_connected ?connect_from ?connect_to)))
 (:action unpush_push_button
  :parameters ( ?a2 - a2_type ?butt - button ?loc - location ?connect_from - location ?connect_to - location)
  :precondition (and 
   (a_pos a3 ?loc)
   (a_pos a2 ?loc)
   (activebutton reedbutton1)
   (activebutton reedbutton2)
   (pressbutton_contemp ?butt ?loc ?connect_from ?connect_to)
  )
  :effect (and
 (when (and (activebutton reedbutton1) (activebutton reedbutton2)) (is_connected ?connect_from ?connect_to))))
 (:action push_red_button1
  :parameters ( ?a2 - a2_type ?butt - button ?loc - location ?connect_from - location ?connect_to - location)
  :precondition (and 
   (a_pos a3 ?loc)
   (a_pos a2 ?loc)
   (pressbutton_contemp ?butt ?loc ?connect_from ?connect_to)
  )
  :effect (and
 (when (not (activebutton reedbutton2)) (activebutton reedbutton2))))
)
```

##### MA-PDDL domain (a3)

```lisp
(define (domain ma_bottons_domain)
 (:requirements :multi-agent :factored-privacy :typing :negative-preconditions :conditional-effects)
 (:types location button ag - object
    a1_type a2_type a3_type - ag
 )
 (:constants
   reedbutton2 reedbutton1 - button
   a3 - a3_type
   a2 - a2_type
 )
 (:predicates
  (is_connected ?l1 - location ?l2 - location)
  (activebutton ?button - button)
  (pressbutton ?button - button ?position - location ?connect_from - location ?connect_to - location)
  (pressbutton_contemp ?button - button ?position - location ?connect_from - location ?connect_to - location)
  (at_gb ?postion - location ?connect_from - location ?connect_to - location)
  (at_rb ?postion - location ?connect_from - location ?connect_to - location)
  (a_pos ?agent - ag ?position - location)
)
 (:action move
  :parameters ( ?a3 - a3_type ?l_from - location ?l_to - location)
  :precondition (and 
   (a_pos  ?a3 ?l_from)
   (is_connected ?l_from ?l_to)
  )
  :effect (and
 (a_pos  ?a3 ?l_to) (not (a_pos  ?a3 ?l_from))))
 (:action push_button
  :parameters ( ?a3 - a3_type ?butt - button ?loc - location ?connect_from - location ?connect_to - location)
  :precondition (and 
   (a_pos  ?a3 ?loc)
   (pressbutton ?butt ?loc ?connect_from ?connect_to)
   (not (activebutton ?butt))
  )
  :effect (and
 (activebutton ?butt) (is_connected ?connect_from ?connect_to)))
 (:action unpush_push_button
  :parameters ( ?a3 - a3_type ?butt - button ?loc - location ?connect_from - location ?connect_to - location)
  :precondition (and 
   (a_pos a3 ?loc)
   (a_pos a2 ?loc)
   (activebutton reedbutton1)
   (activebutton reedbutton2)
   (pressbutton_contemp ?butt ?loc ?connect_from ?connect_to)
  )
  :effect (and
 (when (and (activebutton reedbutton1) (activebutton reedbutton2)) (is_connected ?connect_from ?connect_to))))
 (:action push_red_button2
  :parameters ( ?a3 - a3_type ?butt - button ?loc - location ?connect_from - location ?connect_to - location)
  :precondition (and 
   (a_pos a3 ?loc)
   (a_pos a2 ?loc)
   (pressbutton_contemp ?butt ?loc ?connect_from ?connect_to)
  )
  :effect (and
 (when (not (activebutton reedbutton1)) (activebutton reedbutton1))))
)
```
## hierarchical

### Problems

- [htn_go](#htn_go)
- [htn_go_temporal](#htn_go_temporal)

### htn_go

This example defines `htn_go` with 2 fluent(s), 1 action(s), and 4 object(s). Primary action(s): move. Goal summary: No explicit top-level goal is declared.. Special features: hierarchical tasks and methods, method preconditions.

#### unified-planning

```python
    # basic
    htn = HierarchicalProblem()

    Location = UserType("Location")
    l1 = htn.add_object("l1", Location)
    l2 = htn.add_object("l2", Location)
    l3 = htn.add_object("l3", Location)
    l4 = htn.add_object("l4", Location)

    is_at = Fluent("is_at", position=Location)
    htn.add_fluent(is_at, default_initial_value=False)

    connected = Fluent("connected", l1=Location, l2=Location)
    htn.add_fluent(connected, default_initial_value=False)
    htn.set_initial_value(connected(l1, l2), True)
    htn.set_initial_value(connected(l2, l3), True)
    htn.set_initial_value(connected(l3, l4), True)
    htn.set_initial_value(connected(l4, l3), True)
    htn.set_initial_value(connected(l3, l2), True)
    htn.set_initial_value(connected(l2, l1), True)

    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(is_at(l_from))
    move.add_precondition(connected(l_from, l_to))
    move.add_effect(is_at(l_from), False)
    move.add_effect(is_at(l_to), True)
    htn.add_action(move)
    go = htn.add_task("go", target=Location)

    go_noop = Method("go-noop", target=Location)
    go_noop.set_task(go)
    target = go_noop.parameter("target")
    go_noop.add_precondition(is_at(target))
    htn.add_method(go_noop)

    go_recursive = Method("go-recursive", source=Location, inter=Location, target=Location)
    go_recursive.set_task(go, go_recursive.parameter("target"))
    source = go_recursive.parameter("source")
    inter = go_recursive.parameter("inter")
    target = go_recursive.parameter("target")
    go_recursive.add_precondition(is_at(source))
    go_recursive.add_precondition(connected(source, inter))
    t1 = go_recursive.add_subtask(move, source, inter, ident="move")
    t2 = go_recursive.add_subtask(go, target, ident="go-rec")
    go_recursive.set_ordered(t1, t2)
    htn.add_method(go_recursive)

    go1 = htn.task_network.add_subtask(go, l4, ident="go_l4")
    final_loc = htn.task_network.add_variable("final_loc", Location)
    go2 = htn.task_network.add_subtask(go, final_loc, ident="go_final")
    htn.task_network.add_constraint(Or(Equals(final_loc, l1), Equals(final_loc, l2)))
    htn.task_network.set_strictly_before(go1, go2)

    htn.set_initial_value(is_at(l1), True)
```

#### PDDL domain

```lisp
(define (domain pddl_domain)
 (:requirements :strips :typing :hierarchy :method-preconditions)
 (:types location)
 (:predicates 
             (is_at ?position - location)
             (connected ?l1 - location ?l2 - location)
 )
 (:task go
  :parameters ( ?target - location))
 (:method go-noop
  :parameters ( ?target - location)
  :task (go ?target)
  :precondition (and (is_at ?target)))
 (:method go-recursive
  :parameters ( ?source - location ?inter - location ?target - location)
  :task (go ?target)
  :precondition (and (is_at ?source) (connected ?source ?inter))
  :ordered-subtasks (and
    (move (move ?source ?inter))
    (go-rec (go ?target))))
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and (is_at ?l_from) (connected ?l_from ?l_to))
  :effect (and (not (is_at ?l_from)) (is_at ?l_to)))
)
```

### htn_go_temporal

This example defines `htn_go_temporal` with 2 fluent(s), 1 action(s), and 4 object(s). Primary action(s): durative_move. Goal summary: No explicit top-level goal is declared.. Special features: hierarchical tasks and methods, method preconditions, continuous time.

#### unified-planning

```python
    # basic temporal
    htn_temporal = HierarchicalProblem()
    overall = ClosedTimeInterval(StartTiming(), EndTiming())

    Location = UserType("Location")
    l1 = htn_temporal.add_object("l1", Location)
    l2 = htn_temporal.add_object("l2", Location)
    l3 = htn_temporal.add_object("l3", Location)
    l4 = htn_temporal.add_object("l4", Location)

    is_at = Fluent("is_at", position=Location)
    htn_temporal.add_fluent(is_at, default_initial_value=False)

    connected = Fluent("connected", l1=Location, l2=Location)
    htn_temporal.add_fluent(connected, default_initial_value=False)
    htn_temporal.set_initial_value(connected(l1, l2), True)
    htn_temporal.set_initial_value(connected(l2, l3), True)
    htn_temporal.set_initial_value(connected(l3, l4), True)
    htn_temporal.set_initial_value(connected(l4, l3), True)
    htn_temporal.set_initial_value(connected(l3, l2), True)
    htn_temporal.set_initial_value(connected(l2, l1), True)

    durative_move = DurativeAction("durative_move", l_from=Location, l_to=Location)
    l_from = durative_move.parameter("l_from")
    l_to = durative_move.parameter("l_to")
    durative_move.add_condition(StartTiming(), is_at(l_from))
    durative_move.add_condition(overall, connected(l_from, l_to))
    durative_move.add_effect(EndTiming(), is_at(l_from), False)
    durative_move.add_effect(EndTiming(), is_at(l_to), True)
    durative_move.set_fixed_duration(1)
    htn_temporal.add_action(durative_move)
    go = htn_temporal.add_task("go", target=Location)

    go_noop = Method("go-noop_t", target=Location)
    go_noop.set_task(go)
    target = go_noop.parameter("target")
    go_noop.add_precondition(is_at(target))
    htn_temporal.add_method(go_noop)

    go_recursive = Method("go-recursive_t", source=Location, inter=Location, target=Location)
    go_recursive.set_task(go, go_recursive.parameter("target"))
    source = go_recursive.parameter("source")
    inter = go_recursive.parameter("inter")
    target = go_recursive.parameter("target")
    go_recursive.add_precondition(is_at(source))
    go_recursive.add_precondition(connected(source, inter))
    t1 = go_recursive.add_subtask(durative_move, source, inter)
    t2 = go_recursive.add_subtask(go, target)
    go_recursive.set_ordered(t1, t2)
    htn_temporal.add_method(go_recursive)

    go1 = htn_temporal.task_network.add_subtask(go, l4)
    final_loc = htn_temporal.task_network.add_variable("final_loc", Location)
    go2 = htn_temporal.task_network.add_subtask(go, final_loc)
    htn_temporal.task_network.add_constraint(Or(Equals(final_loc, l1), Equals(final_loc, l2)))
    htn_temporal.task_network.set_strictly_before(go1, go2)
    htn_temporal.task_network.add_constraint(LT(Timing(0, go2.end), GlobalStartTiming(100)))

    htn_temporal.set_initial_value(is_at(l1), True)
```

#### PDDL domain

```lisp
(define (domain pddl_domain)
 (:requirements :strips :typing :durative-actions :hierarchy :method-preconditions)
 (:types location)
 (:predicates 
             (is_at ?position - location)
             (connected ?l1 - location ?l2 - location)
 )
 (:task go
  :parameters ( ?target - location))
 (:method go-noop_t
  :parameters ( ?target - location)
  :task (go ?target)
  :precondition (and (is_at ?target)))
 (:method go-recursive_t
  :parameters ( ?source - location ?inter - location ?target - location)
  :task (go ?target)
  :precondition (and (is_at ?source) (connected ?source ?inter))
  :ordered-subtasks (and
    (_t1 (durative_move ?source ?inter))
    (_t2 (go ?target))))
 (:durative-action durative_move
  :parameters ( ?l_from - location ?l_to - location)
  :duration (= ?duration 1)
  :condition (and 
                 (at start (is_at ?l_from))
                 (at start (connected ?l_from ?l_to))(over all (connected ?l_from ?l_to))(at end (connected ?l_from ?l_to))
             )
  :effect (and
              (at end (not (is_at ?l_from)))
              (at end (is_at ?l_to))
          )
 )
)
```
## realistic

### Problems

- [robot](#robot)
- [robot_fluent_of_user_type](#robot_fluent_of_user_type)
- [robot_no_negative_preconditions](#robot_no_negative_preconditions)
- [robot_decrease](#robot_decrease)
- [robot_loader](#robot_loader)
- [robot_loader_mod](#robot_loader_mod)
- [robot_loader_adv](#robot_loader_adv)
- [robot_locations_connected](#robot_locations_connected)
- [robot_locations_visited](#robot_locations_visited)
- [charge_discharge](#charge_discharge)
- [matchcellar](#matchcellar)
- [timed_connected_locations](#timed_connected_locations)
- [hierarchical_blocks_world](#hierarchical_blocks_world)
- [robot_with_static_fluents_duration](#robot_with_static_fluents_duration)
- [robot_with_static_fluents_duration_timed_goals](#robot_with_static_fluents_duration_timed_goals)
- [robot_holding](#robot_holding)
- [travel](#travel)
- [logistic](#logistic)
- [safe_road](#safe_road)
- [robot_continuous](#robot_continuous)

### robot

This example defines `robot` with 2 fluent(s), 1 action(s), and 2 object(s). Primary action(s): move. Goal summary: robot_at(l2). Special features: real fluents.

#### unified-planning

```python
    # robot
    Location = UserType("Location")
    robot_at = Fluent("robot_at", BoolType(), position=Location)
    battery_charge = Fluent("battery_charge", RealType(0, 100))
    move: Union[InstantaneousAction, DurativeAction] = InstantaneousAction("move", l_from=Location, l_to=Location)
    assert isinstance(move, InstantaneousAction)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(GE(battery_charge, 10))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    move.add_effect(battery_charge, Minus(battery_charge, 10))
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot")
    problem.add_fluent(robot_at)
    problem.add_fluent(battery_charge)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(battery_charge, 100)
    problem.add_goal(robot_at(l2))
```

#### PDDL domain

```lisp
(define (domain robot_domain)
 (:requirements :strips :typing :negative-preconditions :equality :numeric-fluents)
 (:types location)
 (:predicates 
             (robot_at ?position - location)
 )
 (:functions 
             (battery_charge)
 )
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and (<= 10 (battery_charge)) (not (= ?l_from ?l_to)) (robot_at ?l_from) (not (robot_at ?l_to)))
  :effect (and (not (robot_at ?l_from)) (robot_at ?l_to) (assign (battery_charge) (- (battery_charge) 10))))
)
```

### robot_fluent_of_user_type

This example defines `robot_fluent_of_user_type` with 1 fluent(s), 1 action(s), and 4 object(s). Primary action(s): move. Goal summary: (is_at(r1) == l1); (is_at(r2) == l2). Special features: object-valued fluents.

#### unified-planning

```python
    # robot fluent of user_type
    Location = UserType("Location")
    Robot = UserType("Robot")
    is_at = Fluent("is_at", Location, robot=Robot)
    move = InstantaneousAction("move", robot=Robot, l_from=Location, l_to=Location)
    robot = move.parameter("robot")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(Equals(is_at(robot), l_from))
    move.add_precondition(Not(Equals(is_at(robot), l_to)))
    move.add_effect(is_at(robot), l_to)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    r1 = Object("r1", Robot)
    r2 = Object("r2", Robot)
    problem = Problem("robot_fluent_of_user_type")
    problem.add_fluent(is_at)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(r1)
    problem.add_object(r2)
    problem.set_initial_value(is_at(r1), l2)
    problem.set_initial_value(is_at(r2), l1)
    problem.add_goal(Equals(is_at(r1), l1))
    problem.add_goal(Equals(is_at(r2), l2))
```

#### PDDL domain

```text
PDDL domain export unavailable: PDDL supports only boolean and numerical fluents
```

### robot_no_negative_preconditions

This example defines `robot_no_negative_preconditions` with 1 fluent(s), 1 action(s), and 2 object(s). Primary action(s): move. Goal summary: robot_at(l2). Special features: classical planning only.

#### unified-planning

```python
    # robot no negative preconditions
    Location = UserType("location")
    robot_at = Fluent("robot_at", BoolType(), position=Location)
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(robot_at(l_from))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot")
    problem.add_fluent(robot_at)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.add_goal(robot_at(l2))
```

#### PDDL domain

```lisp
(define (domain robot_domain)
 (:requirements :strips :typing)
 (:types location)
 (:predicates 
             (robot_at ?position - location)
 )
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and (robot_at ?l_from))
  :effect (and (not (robot_at ?l_from)) (robot_at ?l_to)))
)
```

### robot_decrease

This example defines `robot_decrease` with 2 fluent(s), 1 action(s), and 2 object(s). Primary action(s): move. Goal summary: robot_at(l2). Special features: real fluents.

#### unified-planning

```python
    # robot decrease
    Location = UserType("Location")
    robot_at = Fluent("robot_at", BoolType(), position=Location)
    battery_charge = Fluent("battery_charge", RealType(0, 100))
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(GE(battery_charge, 10))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    move.add_decrease_effect(battery_charge, 10)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot_decrease")
    problem.add_fluent(robot_at)
    problem.add_fluent(battery_charge)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(battery_charge, 100)
    problem.add_goal(robot_at(l2))
```

#### PDDL domain

```lisp
(define (domain robot_decrease_domain)
 (:requirements :strips :typing :negative-preconditions :equality :numeric-fluents)
 (:types location)
 (:predicates 
             (robot_at ?position - location)
 )
 (:functions 
             (battery_charge)
 )
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and (<= 10 (battery_charge)) (not (= ?l_from ?l_to)) (robot_at ?l_from) (not (robot_at ?l_to)))
  :effect (and (not (robot_at ?l_from)) (robot_at ?l_to) (decrease (battery_charge) 10)))
)
```

### robot_loader

This example defines `robot_loader` with 3 fluent(s), 3 action(s), and 2 object(s). Primary action(s): move, load, unload. Goal summary: cargo_at(l1). Special features: classical planning only.

#### unified-planning

```python
    # robot_loader
    Location = UserType("Location")
    robot_at = Fluent("robot_at", BoolType(), position=Location)
    cargo_at = Fluent("cargo_at", BoolType(), position=Location)
    cargo_mounted = Fluent("cargo_mounted")
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    load = InstantaneousAction("load", loc=Location)
    loc = load.parameter("loc")
    load.add_precondition(cargo_at(loc))
    load.add_precondition(robot_at(loc))
    load.add_precondition(Not(cargo_mounted))
    load.add_effect(cargo_at(loc), False)
    load.add_effect(cargo_mounted, True)
    unload = InstantaneousAction("unload", loc=Location)
    loc = unload.parameter("loc")
    unload.add_precondition(Not(cargo_at(loc)))
    unload.add_precondition(robot_at(loc))
    unload.add_precondition(cargo_mounted)
    unload.add_effect(cargo_at(loc), True)
    unload.add_effect(cargo_mounted, False)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot_loader")
    problem.add_fluent(robot_at)
    problem.add_fluent(cargo_at)
    problem.add_fluent(cargo_mounted)
    problem.add_action(move)
    problem.add_action(load)
    problem.add_action(unload)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(cargo_at(l1), False)
    problem.set_initial_value(cargo_at(l2), True)
    problem.set_initial_value(cargo_mounted, False)
    problem.add_goal(cargo_at(l1))
```

#### PDDL domain

```lisp
(define (domain robot_loader_domain)
 (:requirements :strips :typing :negative-preconditions :equality)
 (:types location)
 (:predicates 
             (robot_at ?position - location)
             (cargo_at ?position - location)
             (cargo_mounted)
 )
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and (not (= ?l_from ?l_to)) (robot_at ?l_from) (not (robot_at ?l_to)))
  :effect (and (not (robot_at ?l_from)) (robot_at ?l_to)))
 (:action load
  :parameters ( ?loc - location)
  :precondition (and (cargo_at ?loc) (robot_at ?loc) (not (cargo_mounted)))
  :effect (and (not (cargo_at ?loc)) (cargo_mounted)))
 (:action unload
  :parameters ( ?loc - location)
  :precondition (and (not (cargo_at ?loc)) (robot_at ?loc) (cargo_mounted))
  :effect (and (cargo_at ?loc) (not (cargo_mounted))))
)
```

### robot_loader_mod

This example defines `robot_loader_mod` with 4 fluent(s), 3 action(s), and 2 object(s). Primary action(s): move, load, unload. Goal summary: cargo_at(l1). Special features: classical planning only.

#### unified-planning

```python
    # robot_loader_mod
    Location = UserType("Location")
    robot_at = Fluent("robot_at", BoolType(), position=Location)
    cargo_at = Fluent("cargo_at", BoolType(), position=Location)
    is_same_location = Fluent("is_same_location", BoolType(), p1=Location, p2=Location)
    cargo_mounted = Fluent("cargo_mounted")
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_precondition(Not(is_same_location(l_from, l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    load = InstantaneousAction("load", loc=Location)
    loc = load.parameter("loc")
    load.add_precondition(cargo_at(loc))
    load.add_precondition(robot_at(loc))
    load.add_precondition(Not(cargo_mounted))
    load.add_effect(cargo_at(loc), False)
    load.add_effect(cargo_mounted, True)
    unload = InstantaneousAction("unload", loc=Location)
    loc = unload.parameter("loc")
    unload.add_precondition(Not(cargo_at(loc)))
    unload.add_precondition(robot_at(loc))
    unload.add_precondition(cargo_mounted)
    unload.add_effect(cargo_at(loc), True)
    unload.add_effect(cargo_mounted, False)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot_loader_mod")
    problem.add_fluent(robot_at, default_initial_value=False)
    problem.add_fluent(cargo_at, default_initial_value=False)
    problem.add_fluent(cargo_mounted, default_initial_value=False)
    problem.add_fluent(is_same_location, default_initial_value=False)
    problem.add_action(move)
    problem.add_action(load)
    problem.add_action(unload)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(cargo_at(l2), True)
    for o in problem.objects(Location):
        problem.set_initial_value(is_same_location(o, o), True)
    problem.add_goal(cargo_at(l1))
```

#### PDDL domain

```lisp
(define (domain robot_loader_mod_domain)
 (:requirements :strips :typing :negative-preconditions)
 (:types location)
 (:predicates 
             (robot_at ?position - location)
             (cargo_at ?position - location)
             (cargo_mounted)
             (is_same_location ?p1 - location ?p2 - location)
 )
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and (robot_at ?l_from) (not (robot_at ?l_to)) (not (is_same_location ?l_from ?l_to)))
  :effect (and (not (robot_at ?l_from)) (robot_at ?l_to)))
 (:action load
  :parameters ( ?loc - location)
  :precondition (and (cargo_at ?loc) (robot_at ?loc) (not (cargo_mounted)))
  :effect (and (not (cargo_at ?loc)) (cargo_mounted)))
 (:action unload
  :parameters ( ?loc - location)
  :precondition (and (not (cargo_at ?loc)) (robot_at ?loc) (cargo_mounted))
  :effect (and (cargo_at ?loc) (not (cargo_mounted))))
)
```

### robot_loader_adv

This example defines `robot_loader_adv` with 3 fluent(s), 3 action(s), and 5 object(s). Primary action(s): move, load, unload. Goal summary: cargo_at(c1, l3); robot_at(r1, l1). Special features: classical planning only.

#### unified-planning

```python
    # robot_loader_adv
    Robot = UserType("Robot")
    Container = UserType("Container")
    Location = UserType("Location")
    robot_at = Fluent("robot_at", BoolType(), robot=Robot, position=Location)
    cargo_at = Fluent("cargo_at", BoolType(), cargo=Container, position=Location)
    cargo_mounted = Fluent("cargo_mounted", BoolType(), cargo=Container, robot=Robot)
    move = InstantaneousAction("move", l_from=Location, l_to=Location, r=Robot)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    r = move.parameter("r")
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(r, l_from))
    move.add_precondition(Not(robot_at(r, l_to)))
    move.add_effect(robot_at(r, l_from), False)
    move.add_effect(robot_at(r, l_to), True)
    load = InstantaneousAction("load", loc=Location, r=Robot, c=Container)
    loc = load.parameter("loc")
    r = load.parameter("r")
    c = load.parameter("c")
    load.add_precondition(cargo_at(c, loc))
    load.add_precondition(robot_at(r, loc))
    load.add_precondition(Not(cargo_mounted(c, r)))
    load.add_effect(cargo_at(c, loc), False)
    load.add_effect(cargo_mounted(c, r), True)
    unload = InstantaneousAction("unload", loc=Location, r=Robot, c=Container)
    loc = unload.parameter("loc")
    r = unload.parameter("r")
    c = unload.parameter("c")
    unload.add_precondition(Not(cargo_at(c, loc)))
    unload.add_precondition(robot_at(r, loc))
    unload.add_precondition(cargo_mounted(c, r))
    unload.add_effect(cargo_at(c, loc), True)
    unload.add_effect(cargo_mounted(c, r), False)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    r1 = Object("r1", Robot)
    c1 = Object("c1", Container)
    problem = Problem("robot_loader_adv")
    problem.add_fluent(robot_at)
    problem.add_fluent(cargo_at)
    problem.add_fluent(cargo_mounted)
    problem.add_action(move)
    problem.add_action(load)
    problem.add_action(unload)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(l3)
    problem.add_object(r1)
    problem.add_object(c1)
    problem.set_initial_value(robot_at(r1, l1), True)
    problem.set_initial_value(robot_at(r1, l2), False)
    problem.set_initial_value(robot_at(r1, l3), False)
    problem.set_initial_value(cargo_at(c1, l1), False)
    problem.set_initial_value(cargo_at(c1, l2), True)
    problem.set_initial_value(cargo_at(c1, l3), False)
    problem.set_initial_value(cargo_mounted(c1, r1), False)
    problem.add_goal(cargo_at(c1, l3))
    problem.add_goal(robot_at(r1, l1))
```

#### PDDL domain

```lisp
(define (domain robot_loader_adv_domain)
 (:requirements :strips :typing :negative-preconditions :equality)
 (:types robot location container)
 (:predicates 
             (robot_at ?robot - robot ?position - location)
             (cargo_at ?cargo - container ?position - location)
             (cargo_mounted ?cargo - container ?robot - robot)
 )
 (:action move
  :parameters ( ?l_from - location ?l_to - location ?r - robot)
  :precondition (and (not (= ?l_from ?l_to)) (robot_at ?r ?l_from) (not (robot_at ?r ?l_to)))
  :effect (and (not (robot_at ?r ?l_from)) (robot_at ?r ?l_to)))
 (:action load
  :parameters ( ?loc - location ?r - robot ?c - container)
  :precondition (and (cargo_at ?c ?loc) (robot_at ?r ?loc) (not (cargo_mounted ?c ?r)))
  :effect (and (not (cargo_at ?c ?loc)) (cargo_mounted ?c ?r)))
 (:action unload
  :parameters ( ?loc - location ?r - robot ?c - container)
  :precondition (and (not (cargo_at ?c ?loc)) (robot_at ?r ?loc) (cargo_mounted ?c ?r))
  :effect (and (cargo_at ?c ?loc) (not (cargo_mounted ?c ?r))))
)
```

### robot_locations_connected

This example defines `robot_locations_connected` with 3 fluent(s), 2 action(s), and 6 object(s). Primary action(s): move, move_2. Goal summary: is_at(l5, r1). Special features: existential conditions, real fluents.

#### unified-planning

```python
    # robot locations connected
    Location = UserType("Location")
    Robot = UserType("Robot")
    is_at = Fluent("is_at", BoolType(), position=Location, robot=Robot)
    battery_charge = Fluent("battery_charge", RealType(0, 100), robot=Robot)
    is_connected = Fluent("is_connected", BoolType(), location_1=Location, location_2=Location)
    move = InstantaneousAction("move", robot=Robot, l_from=Location, l_to=Location)
    robot = move.parameter("robot")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(GE(battery_charge(robot), 10))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(is_at(l_from, robot))
    move.add_precondition(Not(is_at(l_to, robot)))
    move.add_precondition(Or(is_connected(l_from, l_to), is_connected(l_to, l_from)))
    move.add_effect(is_at(l_from, robot), False)
    move.add_effect(is_at(l_to, robot), True)
    move.add_decrease_effect(battery_charge(robot), 10)
    move_2 = InstantaneousAction("move_2", robot=Robot, l_from=Location, l_to=Location)
    robot = move_2.parameter("robot")
    l_from = move_2.parameter("l_from")
    l_to = move_2.parameter("l_to")
    move_2.add_precondition(GE(battery_charge(robot), 15))
    move_2.add_precondition(Not(Equals(l_from, l_to)))
    move_2.add_precondition(is_at(l_from, robot))
    move_2.add_precondition(Not(is_at(l_to, robot)))
    mid_location = Variable("mid_loc", Location)
    # (E (location mid_location)
    # !((mid_location == l_from) || (mid_location == l_to)) && (is_connected(l_from, mid_location) || is_connected(mid_location, l_from)) &&
    # && (is_connected(l_to, mid_location) || is_connected(mid_location, l_to)))
    move_2.add_precondition(
        Exists(
            And(
                Not(Or(Equals(mid_location, l_from), Equals(mid_location, l_to))),
                Or(
                    is_connected(l_from, mid_location),
                    is_connected(mid_location, l_from),
                ),
                Or(is_connected(l_to, mid_location), is_connected(mid_location, l_to)),
            ),
            mid_location,
        )
    )
    move_2.add_effect(is_at(l_from, robot), False)
    move_2.add_effect(is_at(l_to, robot), True)
    move_2.add_decrease_effect(battery_charge(robot), 15)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    r1 = Object("r1", Robot)
    problem = Problem("robot_locations_connected")
    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(battery_charge)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_action(move)
    problem.add_action(move_2)
    problem.add_object(r1)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(l3)
    problem.add_object(l4)
    problem.add_object(l5)
    problem.set_initial_value(is_at(l1, r1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.set_initial_value(battery_charge(r1), 100)
    problem.add_goal(is_at(l5, r1))
```

#### PDDL domain

```lisp
(define (domain robot_locations_connected_domain)
 (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :equality :numeric-fluents :existential-preconditions)
 (:types location robot)
 (:predicates 
             (is_at ?position - location ?robot - robot)
             (is_connected ?location_1 - location ?location_2 - location)
 )
 (:functions 
             (battery_charge ?robot - robot)
 )
 (:action move
  :parameters ( ?robot - robot ?l_from - location ?l_to - location)
  :precondition (and (<= 10 (battery_charge ?robot)) (not (= ?l_from ?l_to)) (is_at ?l_from ?robot) (not (is_at ?l_to ?robot)) (or (is_connected ?l_from ?l_to) (is_connected ?l_to ?l_from)))
  :effect (and (not (is_at ?l_from ?robot)) (is_at ?l_to ?robot) (decrease (battery_charge ?robot) 10)))
 (:action move_2
  :parameters ( ?robot - robot ?l_from - location ?l_to - location)
  :precondition (and (<= 15 (battery_charge ?robot)) (not (= ?l_from ?l_to)) (is_at ?l_from ?robot) (not (is_at ?l_to ?robot)) (exists (?mid_loc - location)
 (and (not (or (= ?mid_loc ?l_from) (= ?mid_loc ?l_to))) (or (is_connected ?l_from ?mid_loc) (is_connected ?mid_loc ?l_from)) (or (is_connected ?l_to ?mid_loc) (is_connected ?mid_loc ?l_to)))))
  :effect (and (not (is_at ?l_from ?robot)) (is_at ?l_to ?robot) (decrease (battery_charge ?robot) 15)))
)
```

### robot_locations_visited

This example defines `robot_locations_visited` with 4 fluent(s), 2 action(s), and 6 object(s). Primary action(s): move, move_2. Goal summary: is_at(l5, r1); Forall (Location visited_loc) visited(visited_loc). Special features: existential conditions, universal conditions, real fluents.

#### unified-planning

```python
    # robot locations visited
    Location = UserType("Location")
    Robot = UserType("Robot")
    is_at = Fluent("is_at", BoolType(), position=Location, robot=Robot)
    battery_charge = Fluent("battery_charge", RealType(0, 100), robot=Robot)
    is_connected = Fluent("is_connected", BoolType(), location_1=Location, location_2=Location)
    visited = Fluent("visited", BoolType(), target=Location)
    move = InstantaneousAction("move", robot=Robot, l_from=Location, l_to=Location)
    robot = move.parameter("robot")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(GE(battery_charge(robot), 10))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(is_at(l_from, robot))
    move.add_precondition(Not(is_at(l_to, robot)))
    move.add_precondition(Or(is_connected(l_from, l_to), is_connected(l_to, l_from)))
    move.add_effect(is_at(l_from, robot), False)
    move.add_effect(is_at(l_to, robot), True)
    move.add_effect(visited(l_to), True)
    move.add_decrease_effect(battery_charge(robot), 10)
    move_2 = InstantaneousAction("move_2", robot=Robot, l_from=Location, l_to=Location)
    robot = move_2.parameter("robot")
    l_from = move_2.parameter("l_from")
    l_to = move_2.parameter("l_to")
    move_2.add_precondition(GE(battery_charge(robot), 15))
    move_2.add_precondition(Not(Equals(l_from, l_to)))
    move_2.add_precondition(is_at(l_from, robot))
    move_2.add_precondition(Not(is_at(l_to, robot)))
    mid_location = Variable("mid_loc", Location)
    # (E (location mid_location)
    # !((mid_location == l_from) || (mid_location == l_to)) && (is_connected(l_from, mid_location) || is_connected(mid_location, l_from)) &&
    # && (is_connected(l_to, mid_location) || is_connected(mid_location, l_to)))
    move_2.add_precondition(
        Exists(
            And(
                Not(Or(Equals(mid_location, l_from), Equals(mid_location, l_to))),
                Or(
                    is_connected(l_from, mid_location),
                    is_connected(mid_location, l_from),
                ),
                Or(is_connected(l_to, mid_location), is_connected(mid_location, l_to)),
            ),
            mid_location,
        )
    )
    move_2.add_effect(is_at(l_from, robot), False)
    move_2.add_effect(is_at(l_to, robot), True)
    move_2.add_effect(visited(l_to), True)
    move_2.add_decrease_effect(battery_charge(robot), 15)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    r1 = Object("r1", Robot)
    problem = Problem("robot_locations_visited")
    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(battery_charge)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_fluent(visited, default_initial_value=False)
    problem.add_action(move)
    problem.add_action(move_2)
    problem.add_object(r1)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(l3)
    problem.add_object(l4)
    problem.add_object(l5)
    problem.set_initial_value(is_at(l1, r1), True)
    problem.set_initial_value(visited(l1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.set_initial_value(battery_charge(r1), 50)
    problem.add_goal(is_at(l5, r1))
    visited_location = Variable("visited_loc", Location)
    problem.add_goal(Forall(visited(visited_location), visited_location))
```

#### PDDL domain

```lisp
(define (domain robot_locations_visited_domain)
 (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :equality :numeric-fluents :existential-preconditions :universal-preconditions)
 (:types location robot)
 (:predicates 
             (is_at ?position - location ?robot - robot)
             (is_connected ?location_1 - location ?location_2 - location)
             (visited ?target - location)
 )
 (:functions 
             (battery_charge ?robot - robot)
 )
 (:action move
  :parameters ( ?robot - robot ?l_from - location ?l_to - location)
  :precondition (and (<= 10 (battery_charge ?robot)) (not (= ?l_from ?l_to)) (is_at ?l_from ?robot) (not (is_at ?l_to ?robot)) (or (is_connected ?l_from ?l_to) (is_connected ?l_to ?l_from)))
  :effect (and (not (is_at ?l_from ?robot)) (is_at ?l_to ?robot) (visited ?l_to) (decrease (battery_charge ?robot) 10)))
 (:action move_2
  :parameters ( ?robot - robot ?l_from - location ?l_to - location)
  :precondition (and (<= 15 (battery_charge ?robot)) (not (= ?l_from ?l_to)) (is_at ?l_from ?robot) (not (is_at ?l_to ?robot)) (exists (?mid_loc - location)
 (and (not (or (= ?mid_loc ?l_from) (= ?mid_loc ?l_to))) (or (is_connected ?l_from ?mid_loc) (is_connected ?mid_loc ?l_from)) (or (is_connected ?l_to ?mid_loc) (is_connected ?mid_loc ?l_to)))))
  :effect (and (not (is_at ?l_from ?robot)) (is_at ?l_to ?robot) (visited ?l_to) (decrease (battery_charge ?robot) 15)))
)
```

### charge_discharge

This example defines `charge_discharge` with 4 fluent(s), 2 action(s), and 0 object(s). Primary action(s): charge, discharge. Goal summary: b_1; b_2; .... Special features: conditional effects.

#### unified-planning

```python
    # charger_discharger
    charger = Fluent("charger")
    b_1 = Fluent("b_1")
    b_2 = Fluent("b_2")
    b_3 = Fluent("b_3")
    charge = InstantaneousAction("charge")
    discharge = InstantaneousAction("discharge")
    charge.add_precondition(Not(charger))
    charge.add_effect(charger, True)
    # !(charger => (b_1 && b_2 && b_3)) in dnf:
    # (charger and !b_1 ) or (charger and !b_2) or (charger and !b_3)
    # which represents the charger is full and at least one battery is not
    discharge.add_precondition(Not(Implies(charger, And(b_1, b_2, b_3))))
    discharge.add_effect(charger, False)
    discharge.add_effect(b_1, True, Not(b_1))
    discharge.add_effect(b_2, True, And(b_1, Not(b_2)))
    discharge.add_effect(b_3, True, And(b_1, b_2, Not(b_3)))
    problem = Problem("charger_discharger")
    problem.add_fluent(charger)
    problem.add_fluent(b_1)
    problem.add_fluent(b_2)
    problem.add_fluent(b_3)
    problem.add_action(charge)
    problem.add_action(discharge)
    problem.set_initial_value(charger, False)
    problem.set_initial_value(b_1, False)
    problem.set_initial_value(b_2, False)
    problem.set_initial_value(b_3, False)
    problem.add_goal(b_1)
    problem.add_goal(b_2)
    problem.add_goal(b_3)
```

#### PDDL domain

```lisp
(define (domain charger_discharger_domain)
 (:requirements :strips :negative-preconditions :disjunctive-preconditions :conditional-effects)
 (:predicates 
             (charger)
             (b_1)
             (b_2)
             (b_3)
 )
 (:action charge
  :parameters ()
  :precondition (and (not (charger)))
  :effect (and (charger)))
 (:action discharge
  :parameters ()
  :precondition (and (not (imply (charger) (and (b_1) (b_2) (b_3)))))
  :effect (and (not (charger)) (when (not (b_1)) (b_1)) (when (and (b_1) (not (b_2))) (b_2)) (when (and (b_1) (b_2) (not (b_3))) (b_3))))
)
```

### matchcellar

This example defines `matchcellar` with 4 fluent(s), 2 action(s), and 6 object(s). Primary action(s): light_match, mend_fuse. Goal summary: fuse_mended(f1); fuse_mended(f2); .... Special features: continuous time.

#### unified-planning

```python
    # matchcellar
    Match = UserType("Match")
    Fuse = UserType("Fuse")
    handfree = Fluent("handfree")
    light = Fluent("light")
    match_used = Fluent("match_used", BoolType(), match=Match)
    fuse_mended = Fluent("fuse_mended", BoolType(), fuse=Fuse)
    light_match = DurativeAction("light_match", m=Match)
    m = light_match.parameter("m")
    light_match.set_fixed_duration(6)
    light_match.add_condition(StartTiming(), Not(match_used(m)))
    light_match.add_effect(StartTiming(), match_used(m), True)
    light_match.add_effect(StartTiming(), light, True)
    light_match.add_effect(EndTiming(), light, False)
    mend_fuse = DurativeAction("mend_fuse", f=Fuse)
    f = mend_fuse.parameter("f")
    mend_fuse.set_fixed_duration(5)
    mend_fuse.add_condition(StartTiming(), handfree)
    mend_fuse.add_condition(ClosedTimeInterval(StartTiming(), EndTiming()), light)
    mend_fuse.add_effect(StartTiming(), handfree, False)
    mend_fuse.add_effect(EndTiming(), fuse_mended(f), True)
    mend_fuse.add_effect(EndTiming(), handfree, True)
    f1 = Object("f1", Fuse)
    f2 = Object("f2", Fuse)
    f3 = Object("f3", Fuse)
    m1 = Object("m1", Match)
    m2 = Object("m2", Match)
    m3 = Object("m3", Match)
    problem = Problem("MatchCellar")
    problem.add_fluent(handfree)
    problem.add_fluent(light)
    problem.add_fluent(match_used, default_initial_value=False)
    problem.add_fluent(fuse_mended, default_initial_value=False)
    problem.add_action(light_match)
    problem.add_action(mend_fuse)
    problem.add_object(f1)
    problem.add_object(f2)
    problem.add_object(f3)
    problem.add_object(m1)
    problem.add_object(m2)
    problem.add_object(m3)
    problem.set_initial_value(light, False)
    problem.set_initial_value(handfree, True)
    problem.add_goal(fuse_mended(f1))
    problem.add_goal(fuse_mended(f2))
    problem.add_goal(fuse_mended(f3))
```

#### PDDL domain

```lisp
(define (domain matchcellar_domain)
 (:requirements :strips :typing :negative-preconditions :durative-actions)
 (:types match fuse)
 (:predicates 
             (handfree)
             (light)
             (match_used ?match - match)
             (fuse_mended ?fuse - fuse)
 )
 (:durative-action light_match
  :parameters ( ?m - match)
  :duration (= ?duration 6)
  :condition (and 
                 (at start (not (match_used ?m)))
             )
  :effect (and
              (at start (match_used ?m))
              (at start (light))
              (at end (not (light)))
          )
 )
 (:durative-action mend_fuse
  :parameters ( ?f - fuse)
  :duration (= ?duration 5)
  :condition (and 
                 (at start (handfree))
                 (at start (light))(over all (light))(at end (light))
             )
  :effect (and
              (at start (not (handfree)))
              (at end (fuse_mended ?f))
              (at end (handfree))
          )
 )
)
```

### timed_connected_locations

This example defines `timed_connected_locations` with 2 fluent(s), 1 action(s), and 5 object(s). Primary action(s): move. Goal summary: is_at(l5). Special features: continuous time, existential conditions.

#### unified-planning

```python
    # timed connected locations
    Location = UserType("Location")
    is_connected = Fluent("is_connected", BoolType(), location_1=Location, location_2=Location)
    is_at = Fluent("is_at", BoolType(), position=Location)
    dur_move = DurativeAction("move", l_from=Location, l_to=Location)
    l_from = dur_move.parameter("l_from")
    l_to = dur_move.parameter("l_to")
    dur_move.set_fixed_duration(6)
    dur_move.add_condition(StartTiming(), is_at(l_from))
    dur_move.add_condition(StartTiming(), Not(is_at(l_to)))
    mid_location = Variable("mid_loc", Location)
    # (E (location mid_location)
    # !((mid_location == l_from) || (mid_location == l_to)) && (is_connected(l_from, mid_location) || is_connected(mid_location, l_from)) &&
    # && (is_connected(l_to, mid_location) || is_connected(mid_location, l_to)))
    dur_move.add_condition(
        ClosedTimeInterval(StartTiming(), EndTiming()),
        Exists(
            And(
                Not(Or(Equals(mid_location, l_from), Equals(mid_location, l_to))),
                Or(
                    is_connected(l_from, mid_location),
                    is_connected(mid_location, l_from),
                ),
                Or(is_connected(l_to, mid_location), is_connected(mid_location, l_to)),
            ),
            mid_location,
        ),
    )
    dur_move.add_condition(
        StartTiming(),
        Exists(
            And(
                Not(Or(Equals(mid_location, l_from), Equals(mid_location, l_to))),
                Or(
                    is_connected(l_from, mid_location),
                    is_connected(mid_location, l_from),
                ),
                Or(is_connected(l_to, mid_location), is_connected(mid_location, l_to)),
            ),
            mid_location,
        ),
    )
    dur_move.add_effect(StartTiming(1), is_at(l_from), False)
    dur_move.add_effect(EndTiming() - 5, is_at(l_to), True)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    problem = Problem("timed_connected_locations")
    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_action(dur_move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(l3)
    problem.add_object(l4)
    problem.add_object(l5)
    problem.set_initial_value(is_at(l1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.add_goal(is_at(l5))
```

#### PDDL domain

```text
PDDL domain export unavailable: PDDL does not support ICE.
ICE are Intermediate Conditions and Effects therefore when an Effect (or Condition) are not at StartTIming(0) or EndTIming(0).
```

### hierarchical_blocks_world

This example defines `hierarchical_blocks_world` with 2 fluent(s), 1 action(s), and 6 object(s). Primary action(s): move. Goal summary: on(block_1, ts_3); on(block_2, block_1); .... Special features: classical planning only.

#### unified-planning

```python
    # hierarchical blocks world
    Entity = UserType("Entity", None)  # None can be avoided
    Location = UserType("Location", Entity)
    Unmovable = UserType("Unmovable", Location)
    TableSpace = UserType("TableSpace", Unmovable)
    Movable = UserType("Movable", Location)
    Block = UserType("Block", Movable)
    clear = Fluent("clear", BoolType(), space=Location)
    on = Fluent("on", BoolType(), object=Movable, space=Location)

    move = InstantaneousAction("move", item=Movable, l_from=Location, l_to=Location)
    item = move.parameter("item")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(clear(item))
    move.add_precondition(clear(l_to))
    move.add_precondition(on(item, l_from))
    move.add_effect(clear(l_from), True)
    move.add_effect(on(item, l_from), False)
    move.add_effect(clear(l_to), False)
    move.add_effect(on(item, l_to), True)

    problem = Problem("hierarchical_blocks_world")
    problem.add_fluent(clear, default_initial_value=False)
    problem.add_fluent(on, default_initial_value=False)
    problem.add_action(move)
    ts_1 = Object("ts_1", TableSpace)
    ts_2 = Object("ts_2", TableSpace)
    ts_3 = Object("ts_3", TableSpace)
    problem.add_objects([ts_1, ts_2, ts_3])
    block_1 = Object("block_1", Block)
    block_2 = Object("block_2", Block)
    block_3 = Object("block_3", Block)
    problem.add_objects([block_1, block_2, block_3])

    # The blocks are all on ts_1, in order block_3 under block_1 under block_2
    problem.set_initial_value(clear(ts_2), True)
    problem.set_initial_value(clear(ts_3), True)
    problem.set_initial_value(clear(block_2), True)
    problem.set_initial_value(on(block_3, ts_1), True)
    problem.set_initial_value(on(block_1, block_3), True)
    problem.set_initial_value(on(block_2, block_1), True)

    # We want them on ts_3 in order block_3 on block_2 on block_1
    problem.add_goal(on(block_1, ts_3))
    problem.add_goal(on(block_2, block_1))
    problem.add_goal(on(block_3, block_2))

```

#### PDDL domain

```lisp
(define (domain hierarchical_blocks_world_domain)
 (:requirements :strips :typing)
 (:types
    entity - object
    location - entity
    movable unmovable - location
    tablespace - unmovable
    block - movable
 )
 (:predicates 
             (clear ?space - location)
             (on ?object - movable ?space - location)
 )
 (:action move
  :parameters ( ?item - movable ?l_from - location ?l_to - location)
  :precondition (and (clear ?item) (clear ?l_to) (on ?item ?l_from))
  :effect (and (clear ?l_from) (not (on ?item ?l_from)) (not (clear ?l_to)) (on ?item ?l_to)))
)
```

### robot_with_static_fluents_duration

This example defines `robot_with_static_fluents_duration` with 3 fluent(s), 1 action(s), and 6 object(s). Primary action(s): move. Goal summary: is_at(l5, r1). Special features: continuous time.

#### unified-planning

```python
    # robot with action duration expressed using static fluents
    problem = Problem("robot_with_durative_action")

    Location = UserType("Location")
    Robot = UserType("Robot")

    is_at = Fluent("is_at", BoolType(), position=Location, robot=Robot)
    is_connected = Fluent("is_connected", BoolType(), l_from=Location, l_to=Location)
    distance = Fluent("distance", RealType(), l_from=Location, l_to=Location)
    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_fluent(distance, default_initial_value=1)

    dur_move = DurativeAction("move", r=Robot, l_from=Location, l_to=Location)
    r = dur_move.parameter("r")
    l_from = dur_move.parameter("l_from")
    l_to = dur_move.parameter("l_to")
    dur_move.set_fixed_duration((distance(l_from, l_to)))
    dur_move.add_condition(StartTiming(), is_connected(l_from, l_to))
    dur_move.add_condition(StartTiming(), is_at(l_from, r))
    dur_move.add_condition(StartTiming(), Not(is_at(l_to, r)))
    dur_move.add_effect(StartTiming(), is_at(l_from, r), False)
    dur_move.add_effect(EndTiming(), is_at(l_to, r), True)
    problem.add_action(dur_move)

    r1 = Object("r1", Robot)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    problem.add_objects([r1, l1, l2, l3, l4, l5])

    problem.set_initial_value(is_at(l1, r1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.set_initial_value(distance(l1, l2), 10)
    problem.set_initial_value(distance(l2, l3), 10)
    problem.set_initial_value(distance(l3, l4), 10)
    problem.set_initial_value(distance(l4, l5), 10)

    problem.add_goal(is_at(l5, r1))

```

#### PDDL domain

```lisp
(define (domain robot_with_durative_action_domain)
 (:requirements :strips :typing :negative-preconditions :durative-actions)
 (:types location robot)
 (:predicates 
             (is_at ?position - location ?robot - robot)
             (is_connected ?l_from - location ?l_to - location)
 )
 (:functions 
             (distance ?l_from - location ?l_to - location)
 )
 (:durative-action move
  :parameters ( ?r - robot ?l_from - location ?l_to - location)
  :duration (= ?duration (distance ?l_from ?l_to))
  :condition (and 
                 (at start (is_connected ?l_from ?l_to))
                 (at start (is_at ?l_from ?r))
                 (at start (not (is_at ?l_to ?r)))
             )
  :effect (and
              (at start (not (is_at ?l_from ?r)))
              (at end (is_at ?l_to ?r))
          )
 )
)
```

### robot_with_static_fluents_duration_timed_goals

This example defines `robot_with_static_fluents_duration_timed_goals` with 3 fluent(s), 1 action(s), and 6 object(s). Primary action(s): move. Goal summary: is_at(l5, r1). Special features: continuous time, timed goals.

#### unified-planning

```python
    # Robot with timed_goals (extension of the previous problem with timed goals)
    problem = problem.clone()
    name = "robot_with_static_fluents_duration_timed_goals"
    problem.name = name
    problem.add_timed_goal(GlobalStartTiming() + 50, is_at(l5, r1))
```

#### PDDL domain

```text
PDDL domain export unavailable: PDDL does not support timed goals.
```

### robot_holding

This example defines `robot_holding` with 6 fluent(s), 3 action(s), and 15 object(s). Primary action(s): pick_up, put_down, move. Goal summary: obj_on(o0, t5); obj_on(o1, t2). Special features: continuous time.

#### unified-planning

```python
    # robot holding
    Room = UserType("Room")
    Obj = UserType("Obj")
    Table = UserType("Table")

    robot_in = Fluent("robot_in", robot=Robot, room=Room)
    connect = Fluent("connect", l_from=Room, l_to=Room)
    handvoid = Fluent("handvoid", robot=Robot)
    holding = Fluent("holding", robot=Robot, obj=Obj)
    obj_on = Fluent("obj_on", obj=Obj, table=Table)
    inside = Fluent("inside", table=Table, room=Room)

    pick_up = DurativeAction("pick_up", robot=Robot, obj=Obj, table=Table, room=Room)
    pick_up.set_fixed_duration(2)
    robot = pick_up.parameter("robot")
    obj = pick_up.parameter("obj")
    table = pick_up.parameter("table")
    room = pick_up.parameter("room")
    pick_up.add_condition(StartTiming(), handvoid(robot))
    pick_up.add_condition(StartTiming(), inside(table, room))
    pick_up.add_condition(StartTiming(), obj_on(obj, table))
    pick_up.add_condition(StartTiming(), Not(holding(robot, obj)))
    pick_up.add_condition(ClosedTimeInterval(StartTiming(), EndTiming()), robot_in(robot, room))
    pick_up.add_effect(StartTiming(), handvoid(robot), False)
    pick_up.add_effect(StartTiming(), obj_on(obj, table), False)
    pick_up.add_effect(EndTiming(), holding(robot, obj), True)

    put_down = DurativeAction("put_down", robot=Robot, obj=Obj, table=Table, room=Room)
    put_down.set_fixed_duration(2)
    robot = put_down.parameter("robot")
    obj = put_down.parameter("obj")
    table = put_down.parameter("table")
    room = put_down.parameter("room")
    put_down.add_condition(StartTiming(), Not(handvoid(robot)))
    put_down.add_condition(StartTiming(), inside(table, room))
    put_down.add_condition(StartTiming(), Not(obj_on(obj, table)))
    put_down.add_condition(StartTiming(), holding(robot, obj))
    put_down.add_condition(ClosedTimeInterval(StartTiming(), EndTiming()), robot_in(robot, room))
    put_down.add_effect(EndTiming(), obj_on(obj, table), True)
    put_down.add_effect(StartTiming(), holding(robot, obj), False)
    put_down.add_effect(EndTiming(), handvoid(robot), True)

    move = DurativeAction("move", robot=Robot, l_from=Room, l_to=Room)
    move.set_fixed_duration(5)
    robot = move.parameter("robot")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_condition(StartTiming(), robot_in(robot, l_from))
    move.add_condition(StartTiming(), Or(connect(l_from, l_to), connect(l_to, l_from)))
    move.add_effect(StartTiming(), robot_in(robot, l_from), False)
    move.add_effect(EndTiming(), robot_in(robot, l_to), True)

    problem = Problem("robot_holding")
    problem.add_fluent(robot_in, default_initial_value=False)
    problem.add_fluent(connect, default_initial_value=False)
    problem.add_fluent(handvoid, default_initial_value=True)
    problem.add_fluent(holding, default_initial_value=False)
    problem.add_fluent(obj_on, default_initial_value=False)
    problem.add_fluent(inside, default_initial_value=False)
    problem.add_action(pick_up)
    problem.add_action(put_down)
    problem.add_action(move)
    NLOC = 6
    locations = [Object("l%s" % i, Room) for i in range(NLOC)]
    problem.add_objects(locations)
    l0, l1, l2, l3, l4, l5 = locations
    NTAB = 6
    tables = [Object("t%s" % i, Table) for i in range(NTAB)]
    problem.add_objects(tables)
    t0, t1, t2, t3, t4, t5 = tables

    rob = Object("r", Robot)
    problem.add_object(rob)
    objects = [Object("o%s" % i, Obj) for i in range(2)]
    problem.add_objects(objects)
    o0, o1 = objects
    for i in range(NLOC - 1):
        problem.set_initial_value(connect(locations[i], locations[i + 1]), True)
    for i in range(NLOC):
        problem.set_initial_value(inside(tables[i], locations[i]), True)
    problem.set_initial_value(robot_in(rob, locations[0]), True)
    problem.set_initial_value(obj_on(objects[0], tables[0]), True)
    problem.set_initial_value(obj_on(objects[1], tables[1]), True)
    problem.add_goal(obj_on(objects[0], tables[-1]))
    problem.add_goal(obj_on(objects[1], tables[2]))

```

#### PDDL domain

```lisp
(define (domain robot_holding_domain)
 (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :durative-actions)
 (:types robot room obj table)
 (:predicates 
             (robot_in ?robot - robot ?room - room)
             (connect ?l_from - room ?l_to - room)
             (handvoid ?robot - robot)
             (holding ?robot - robot ?obj - obj)
             (obj_on ?obj - obj ?table - table)
             (inside ?table - table ?room - room)
 )
 (:durative-action pick_up
  :parameters ( ?robot - robot ?obj - obj ?table - table ?room - room)
  :duration (= ?duration 2)
  :condition (and 
                 (at start (handvoid ?robot))
                 (at start (inside ?table ?room))
                 (at start (obj_on ?obj ?table))
                 (at start (not (holding ?robot ?obj)))
                 (at start (robot_in ?robot ?room))(over all (robot_in ?robot ?room))(at end (robot_in ?robot ?room))
             )
  :effect (and
              (at start (not (handvoid ?robot)))
              (at start (not (obj_on ?obj ?table)))
              (at end (holding ?robot ?obj))
          )
 )
 (:durative-action put_down
  :parameters ( ?robot - robot ?obj - obj ?table - table ?room - room)
  :duration (= ?duration 2)
  :condition (and 
                 (at start (not (handvoid ?robot)))
                 (at start (inside ?table ?room))
                 (at start (not (obj_on ?obj ?table)))
                 (at start (holding ?robot ?obj))
                 (at start (robot_in ?robot ?room))(over all (robot_in ?robot ?room))(at end (robot_in ?robot ?room))
             )
  :effect (and
              (at end (obj_on ?obj ?table))
              (at end (handvoid ?robot))
              (at start (not (holding ?robot ?obj)))
          )
 )
 (:durative-action move
  :parameters ( ?robot - robot ?l_from - room ?l_to - room)
  :duration (= ?duration 5)
  :condition (and 
                 (at start (robot_in ?robot ?l_from))
                 (at start (or (connect ?l_from ?l_to) (connect ?l_to ?l_from)))
             )
  :effect (and
              (at start (not (robot_in ?robot ?l_from)))
              (at end (robot_in ?robot ?l_to))
          )
 )
)
```

### travel

This example defines `travel` with 4 fluent(s), 1 action(s), and 5 object(s). Primary action(s): move. Goal summary: is_at(l5). Special features: integer fluents, 1 quality metric(s).

#### unified-planning

```python
    # travel
    problem = Problem("travel")

    Location = UserType("Location")

    is_at = Fluent("is_at", BoolType(), position=Location)
    is_connected = Fluent("is_connected", BoolType(), l_from=Location, l_to=Location)
    travel_time = Fluent("travel_time", IntType(0, 500), l_from=Location, l_to=Location)
    total_travel_time = Fluent("total_travel_time", IntType())

    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_fluent(travel_time, default_initial_value=500)
    problem.add_fluent(total_travel_time, default_initial_value=0)

    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(is_at(l_from))
    move.add_precondition(is_connected(l_from, l_to))
    move.add_effect(is_at(l_from), False)
    move.add_effect(is_at(l_to), True)
    move.add_increase_effect(total_travel_time, travel_time(l_from, l_to))
    problem.add_action(move)

    problem.add_quality_metric(up.model.metrics.MinimizeExpressionOnFinalState(total_travel_time()))

    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    problem.add_objects([l1, l2, l3, l4, l5])

    problem.set_initial_value(is_at(l1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l1, l3), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.set_initial_value(is_connected(l3, l5), True)
    problem.set_initial_value(travel_time(l1, l2), 60)
    problem.set_initial_value(travel_time(l2, l3), 70)
    problem.set_initial_value(travel_time(l1, l3), 100)
    problem.set_initial_value(travel_time(l3, l4), 100)
    problem.set_initial_value(travel_time(l4, l5), 99)
    problem.set_initial_value(travel_time(l3, l5), 200)

    problem.add_goal(is_at(l5))

```

#### PDDL domain

```lisp
(define (domain travel_domain)
 (:requirements :strips :typing :numeric-fluents)
 (:types location)
 (:predicates 
             (is_at ?position - location)
             (is_connected ?l_from - location ?l_to - location)
 )
 (:functions 
             (travel_time ?l_from - location ?l_to - location)
             (total_travel_time)
 )
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and (is_at ?l_from) (is_connected ?l_from ?l_to))
  :effect (and (not (is_at ?l_from)) (is_at ?l_to) (increase (total_travel_time) (travel_time ?l_from ?l_to))))
)
```

### logistic

This example defines `logistic` with 6 fluent(s), 3 action(s), and 8 object(s). Primary action(s): move, load, unload. Goal summary: package_at(p1, l4); package_at(p2, l4). Special features: continuous time.

#### unified-planning

```python
    # logistic
    problem = Problem("logistic")

    Location = UserType("Location")
    Robot = UserType("Robot")
    Package = UserType("Package")

    robot_at = Fluent("robot_at", robot=Robot, position=Location)
    package_at = Fluent("package_at", package=Package, position=Location)
    package_loaded = Fluent("package_loaded", package=Package, robot=Robot)
    is_connected = Fluent("is_connected", l_from=Location, l_to=Location)
    distance = Fluent("distance", IntType(0, 500), l_from=Location, l_to=Location)
    velocity = Fluent("velocity", RealType(), robot=Robot)

    problem.add_fluent(robot_at, default_initial_value=False)
    problem.add_fluent(package_at, default_initial_value=False)
    problem.add_fluent(package_loaded, default_initial_value=False)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_fluent(distance, default_initial_value=500)
    problem.add_fluent(velocity, default_initial_value=Fraction(1))

    n_robots = 2
    robots = [Object(f"r{i}", Robot) for i in range(1, n_robots + 1)]
    n_packages = 2
    packages = [Object(f"p{i}", Package) for i in range(1, n_packages + 1)]
    n_locations = 4
    locations = [Object(f"l{i}", Location) for i in range(1, n_locations + 1)]
    problem.add_objects(chain(robots, packages, locations))

    distances = [8, 5, 6]
    assert distances  # avoid infinite loop below
    while len(distances) < n_locations - 1:
        distances.extend(distances)

    velocities = [Fraction(1, 2), Fraction(1)]
    assert velocities  # avoid infinite loop below
    while len(velocities) < n_robots:
        velocities.extend(velocities)

    at_start = StartTiming()
    at_end = EndTiming()
    overall = ClosedTimeInterval(at_start, at_end)

    move = DurativeAction("move", robot=Robot, l_from=Location, l_to=Location)
    assert isinstance(move, DurativeAction)
    robot = move.parameter("robot")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_condition(at_start, robot_at(robot, l_from))
    move.add_condition(overall, is_connected(l_from, l_to))
    for rob in robots:
        move.add_condition(at_end, Not(robot_at(rob, l_to)))
    move.add_effect(at_start, robot_at(robot, l_from), False)
    move.add_effect(at_end, robot_at(robot, l_to), True)
    move.set_fixed_duration(distance(l_from, l_to) / velocity(robot))
    problem.add_action(move)

    load = InstantaneousAction("load", package=Package, robot=Robot, position=Location)
    load.add_precondition(package_at(load.package, load.position))
    load.add_precondition(robot_at(load.robot, load.position))
    for p in packages:
        load.add_precondition(Not(package_loaded(p, load.robot)))
    load.add_effect(package_at(load.package, load.position), False)
    load.add_effect(package_loaded(load.package, load.robot), True)
    problem.add_action(load)

    unload = InstantaneousAction("unload", package=Package, robot=Robot, position=Location)
    unload.add_precondition(package_loaded(unload.package, unload.robot))
    unload.add_precondition(robot_at(unload.robot, unload.position))
    is_last_position = Equals(unload.position, locations[-1])
    for p in packages:
        unload.add_precondition(Or(is_last_position, Not(package_at(p, unload.position))))
    unload.add_effect(package_loaded(unload.package, unload.robot), False)
    unload.add_effect(package_at(unload.package, unload.position), True)
    problem.add_action(unload)

    for rob, vel in zip(robots, velocities):
        problem.set_initial_value(robot_at(rob, locations[0]), True)
        problem.set_initial_value(velocity(rob), vel)
    for p in packages:
        problem.set_initial_value(package_at(p, locations[0]), True)
    for l1, l2, d in zip(locations[:-1], locations[1:], distances):
        problem.set_initial_value(is_connected(l1, l2), True)
        problem.set_initial_value(is_connected(l2, l1), True)
        problem.set_initial_value(distance(l1, l2), d)
        problem.set_initial_value(distance(l2, l1), d)

    for p in packages:
        problem.add_goal(package_at(p, locations[-1]))

    r1, r2 = robots
    l1, l2, l3, l4 = locations
    p1, p2 = packages
```

#### PDDL domain

```lisp
(define (domain logistic_domain)
 (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :equality :durative-actions)
 (:types robot location package)
 (:constants
   r2 r1 - robot
   p1 p2 - package
   l4 - location
 )
 (:predicates 
             (robot_at ?robot - robot ?position - location)
             (package_at ?package - package ?position - location)
             (package_loaded ?package - package ?robot - robot)
             (is_connected ?l_from - location ?l_to - location)
 )
 (:functions 
             (distance ?l_from - location ?l_to - location)
             (velocity ?robot - robot)
 )
 (:durative-action move
  :parameters ( ?robot - robot ?l_from - location ?l_to - location)
  :duration (= ?duration (/ (distance ?l_from ?l_to) (velocity ?robot)))
  :condition (and 
                 (at start (robot_at ?robot ?l_from))
                 (at start (is_connected ?l_from ?l_to))(over all (is_connected ?l_from ?l_to))(at end (is_connected ?l_from ?l_to))
                 (at end (not (robot_at r1 ?l_to)))
                 (at end (not (robot_at r2 ?l_to)))
             )
  :effect (and
              (at start (not (robot_at ?robot ?l_from)))
              (at end (robot_at ?robot ?l_to))
          )
 )
 (:action load
  :parameters ( ?package - package ?robot - robot ?position - location)
  :precondition (and (package_at ?package ?position) (robot_at ?robot ?position) (not (package_loaded p1 ?robot)) (not (package_loaded p2 ?robot)))
  :effect (and (not (package_at ?package ?position)) (package_loaded ?package ?robot)))
 (:action unload
  :parameters ( ?package - package ?robot - robot ?position - location)
  :precondition (and (package_loaded ?package ?robot) (robot_at ?robot ?position) (or (= ?position l4) (not (package_at p1 ?position))) (or (= ?position l4) (not (package_at p2 ?position))))
  :effect (and (not (package_loaded ?package ?robot)) (package_at ?package ?position)))
)
```

### safe_road

This example defines `safe_road` with 2 fluent(s), 2 action(s), and 3 object(s). Primary action(s): check, natural_disaster. Goal summary: disaster_happened; Forall (Location lx, Location ly) safe(lx, ly). Special features: universal conditions.

#### unified-planning

```python
    # safe_road
    problem = Problem("safe_road")

    Location = UserType("Location")

    safe = Fluent("safe", l_from=Location, l_to=Location)
    disaster_happened = Fluent("disaster_happened")

    problem.add_fluent(safe, default_initial_value=True)
    problem.add_fluent(disaster_happened, default_initial_value=False)

    check = InstantaneousAction("check", l_from=Location, l_to=Location)
    l_from = check.parameter("l_from")
    l_to = check.parameter("l_to")
    check.add_effect(safe(l_from, l_to), True)
    problem.add_action(check)

    natural_disaster = InstantaneousAction("natural_disaster")
    lx, ly = Variable("lx", Location), Variable("ly", Location)
    natural_disaster.add_effect(disaster_happened, True)
    natural_disaster.add_effect(safe(lx, ly), False, forall=[lx, ly])
    problem.add_action(natural_disaster)

    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    locations = [l1, l2, l3]
    problem.add_objects(locations)

    problem.add_goal(disaster_happened)
    problem.add_goal(Forall(safe(lx, ly), lx, ly))

```

#### PDDL domain

```lisp
(define (domain safe_road_domain)
 (:requirements :strips :typing :universal-preconditions)
 (:types location)
 (:predicates 
             (safe ?l_from - location ?l_to - location)
             (disaster_happened)
 )
 (:action check
  :parameters ( ?l_from - location ?l_to - location)
  :effect (and (safe ?l_from ?l_to)))
 (:action natural_disaster
  :parameters ()
  :effect (and (disaster_happened)(forall (?lx - location ?ly - location) (not (safe ?lx ?ly)))))
)
```

### robot_continuous

This example defines `robot_continuous` with 3 fluent(s), 1 action(s), and 2 object(s). Primary action(s): move. Goal summary: robot_at(l2); (battery_charge == 90). Special features: continuous time, real fluents.

#### unified-planning

```python
    # robot_continuous
    Location = UserType("Location")
    connected = Fluent("connected", BoolType(), l_from=Location, l_to=Location)
    robot_at = Fluent("robot_at", BoolType(), position=Location)
    battery_charge = Fluent("battery_charge", RealType(0, 100))
    move = DurativeAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.set_fixed_duration(10)
    move.add_condition(StartTiming(), connected(l_from, l_to))
    move.add_condition(StartTiming(), robot_at(l_from))
    move.add_effect(StartTiming(), robot_at(l_from), False)
    move.add_effect(EndTiming(), robot_at(l_to), True)
    move.add_decrease_continuous_effect(ClosedTimeInterval(StartTiming(), EndTiming()), battery_charge, 1)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot_continuous")
    problem.add_fluent(robot_at, default_initial_value=False)
    problem.add_fluent(connected, default_initial_value=False)
    problem.add_fluent(battery_charge, default_initial_value=100)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(connected(l1, l2), True)
    problem.set_initial_value(robot_at(l1), True)
    problem.add_goal(robot_at(l2))
    problem.add_goal(Equals(battery_charge, 90))
```

#### PDDL domain

```lisp
(define (domain robot_continuous_domain)
 (:requirements :strips :typing :equality :numeric-fluents :durative-actions :continuous-effects)
 (:types location)
 (:predicates 
             (robot_at ?position - location)
             (connected ?l_from - location ?l_to - location)
 )
 (:functions 
             (battery_charge)
 )
 (:durative-action move
  :parameters ( ?l_from - location ?l_to - location)
  :duration (= ?duration 10)
  :condition (and 
                 (at start (connected ?l_from ?l_to))
                 (at start (robot_at ?l_from))
             )
  :effect (and
              (at start (not (robot_at ?l_from)))
              (at end (robot_at ?l_to))
 (decrease (battery_charge) (* #t 1))
          )
 )
)
```
## tamp

### Problems

- [tamp_feasible](#tamp_feasible)

### tamp_feasible

This example defines `tamp_feasible` with 1 fluent(s), 1 action(s), and 3 object(s). Primary action(s): move. Goal summary: robot_at(r1, c2). Special features: classical planning only.

#### unified-planning

```python
    # assumptions:
    # 1. the world is deterministic
    # 2. the world is completely known
    # 3. the moveable object (e.g., the robot) moves in a map composed of fixed obstacles
    # 4. there is one common reference system (e.g., /world (0.0, 0.0, 0.0)) - that is the reference system of the map

    Robot = MovableType("robot")

    # representation of the free and occupied working space, fixed obstacles are located on the occupied areas (e.g., Octomap)
    map = OccupancyMap(os.path.join(FILE_PATH, "..", "tamp", "test-map.yaml"), (0, 0))

    # representation of the state of a movable object
    # the input is equals to the number of variables useful to define this state
    # (e.g., 3 = [x, y, yaw] - N = [N-DOFs of a robot])
    RobotConfig = ConfigurationType("robot_config", map, 3)

    robot_at = Fluent("robot_at", BoolType(), robot=Robot, configuration=RobotConfig)

    # configurations in the map
    # map and RobotConfig added for consistency check
    # e.g., `c1` is a configuration expressed via 5 variables and is a collision free configuration in `map`
    c1 = ConfigurationObject("c1", RobotConfig, (4.0, 26.0, 3 * math.pi / 2.0))
    c2 = ConfigurationObject("c2", RobotConfig, (26.0, 26.0, math.pi / 2.0))

    r1 = MovableObject(
        "r1",
        Robot,
        footprint=[(-1.0, 0.5), (1.0, 0.5), (1.0, -0.5), (-1.0, -0.5)],
        motion_model=MotionModels.REEDSSHEPP,
        parameters={"turning_radius": 4.0},
    )

    move = InstantaneousMotionAction("move", robot=Robot, c_from=RobotConfig, c_to=RobotConfig)
    robot = move.parameter("robot")
    c_from = move.parameter("c_from")
    c_to = move.parameter("c_to")
    move.add_precondition(robot_at(robot, c_from))
    move.add_effect(robot_at(robot, c_from), False)
    move.add_effect(robot_at(robot, c_to), True)

    # there exists a motion control in your motion model that lets the moveable object moves from c_from to [c_to],
    # where [c_to] is a set of waypoints in your map
    move.add_motion_constraint(Waypoints(robot, c_from, [c_to]))

    problem = Problem("robot")
    problem.add_fluent(robot_at)
    problem.add_action(move)
    problem.add_object(c1)
    problem.add_object(c2)
    problem.add_object(r1)
    problem.set_initial_value(robot_at(r1, c1), True)
    problem.set_initial_value(robot_at(r1, c2), False)
    problem.add_goal(robot_at(r1, c2))

    motion_paths: Dict[MotionConstraint, Path] = {
        Waypoints(ObjectExp(r1), ObjectExp(c1), [ObjectExp(c2)]): ReedsSheppPath(
            [
                ((4.0, 26.0, -1.570796326794897), 0.0),
                ((4.024090241148528, 25.495925130590077, -1.5068310794722208), 0.0),
                ((4.0563552195272035, 24.992199074678314, -1.5068310794722208), 0.0),
                ((4.088620197905879, 24.488473018766552, -1.5068310794722208), 0.0),
                ((4.120885176284554, 23.98474696285479, -1.5068310794722208), 0.0),
                ((4.15315015466323, 23.481020906943026, -1.5068310794722208), 0.0),
                ((4.185415133041905, 22.977294851031264, -1.5068310794722208), 0.0),
                ((4.217680111420581, 22.473568795119505, -1.5068310794722208), 0.0),
                ((4.249945089799256, 21.969842739207742, -1.5068310794722208), 0.0),
                ((4.282210068177932, 21.46611668329598, -1.5068310794722208), 0.0),
                ((4.314475046556607, 20.962390627384217, -1.5068310794722208), 0.0),
                ((4.346740024935283, 20.458664571472454, -1.5068310794722208), 0.0),
                ((4.379005003313958, 19.95493851556069, -1.5068310794722208), 0.0),
                ((4.411269981692634, 19.45121245964893, -1.5068310794722208), 0.0),
                ((4.443534960071309, 18.947486403737166, -1.5068310794722208), 0.0),
                ((4.475799938449985, 18.443760347825403, -1.5068310794722208), 0.0),
                ((4.50806491682866, 17.94003429191364, -1.5068310794722208), 0.0),
                ((4.540329895207336, 17.436308236001878, -1.5068310794722208), 0.0),
                ((4.572594873586011, 16.93258218009012, -1.5068310794722208), 0.0),
                ((4.604859851964687, 16.428856124178356, -1.5068310794722208), 0.0),
                ((4.637124830343362, 15.925130068266593, -1.5068310794722208), 0.0),
                ((4.669389808722038, 15.42140401235483, -1.5068310794722208), 0.0),
                ((4.701654787100713, 14.917677956443068, -1.5068310794722208), 0.0),
                ((4.7339197654793885, 14.413951900531307, -1.5068310794722208), 0.0),
                ((4.766184743858064, 13.910225844619545, -1.5068310794722208), 0.0),
                ((4.7984497222367395, 13.406499788707784, -1.5068310794722208), 0.0),
                ((4.830714700615415, 12.902773732796021, -1.5068310794722208), 0.0),
                ((4.8629796789940904, 12.399047676884257, -1.5068310794722208), 0.0),
                ((4.895244657372766, 11.895321620972497, -1.5068310794722208), 0.0),
                ((4.927509635751441, 11.391595565060733, -1.5068310794722208), 0.0),
                ((4.959774614130117, 10.88786950914897, -1.5068310794722208), 0.0),
                ((4.992039592508792, 10.384143453237211, -1.5068310794722208), 0.0),
                ((5.024304570887468, 9.880417397325445, -1.5068310794722208), 0.0),
                ((5.056569549266143, 9.376691341413682, -1.5068310794722208), 0.0),
                ((5.088834527644819, 8.87296528550192, -1.5068310794722208), 0.0),
                ((5.121099506023494, 8.36923922959016, -1.5068310794722208), 0.0),
                ((5.15336448440217, 7.865513173678394, -1.5068310794722208), 0.0),
                ((5.185629462780845, 7.361787117766635, -1.5068310794722208), 0.0),
                ((5.217894441159521, 6.8580610618548725, -1.5068310794722208), 0.0),
                ((5.250159419538196, 6.35433500594311, -1.5068310794722208), 0.0),
                ((5.28389412984352, 5.850716451420794, -1.4796862055437154), 0.0),
                ((5.361370800830223, 5.352278468547841, -1.3534966239030854), 0.0),
                ((5.500962312965778, 4.867554560475057, -1.2273070422624555), 0.0),
                ((5.700448785554974, 4.4042531417727595, -1.1011174606218255), 0.0),
                ((5.95665784684912, 3.969741951780584, -0.9749278789811946), 0.0),
                ((6.26551508329395, 3.5709308877248027, -0.8487382973405646), 0.0),
                ((6.622108833669736, 3.214162118757322, -0.7225487156999346), 0.0),
                ((7.020768297722351, 2.9051092283988567, -0.5963591340593051), 0.0),
                ((7.453357036711573, 2.64960059460526, -0.4706734581230916), 0.0),
                ((7.914562785506687, 2.4503346007134454, -0.3449877821868781), 0.0),
                ((8.397109513815677, 2.310454887954066, -0.2193021062506646), 0.0),
                ((8.893384513814182, 2.232168213354619, -0.0936164303144511), 0.0),
                ((9.395558499023023, 2.2167096357090066, 0.03206924562176239), 0.0),
                ((9.89711361598862, 2.2506721872123165, 0.07491313757543272), 0.0),
                ((10.398446288798315, 2.288299004007954, 0.07491313757543272), 0.0),
                ((10.89977896160801, 2.325925820803591, 0.07491313757543272), 0.0),
                ((11.401111634417706, 2.3635526375992284, 0.07491313757543272), 0.0),
                ((11.902444307227402, 2.4011794543948657, 0.07491313757543272), 0.0),
                ((12.403776980037101, 2.4388062711905034, 0.07491313757543272), 0.0),
                ((12.905109652846793, 2.4764330879861403, 0.07491313757543272), 0.0),
                ((13.40644232565649, 2.514059904781778, 0.07491313757543272), 0.0),
                ((13.907774998466186, 2.551686721577415, 0.07491313757543272), 0.0),
                ((14.409107671275882, 2.5893135383730526, 0.07491313757543272), 0.0),
                ((14.910440344085577, 2.62694035516869, 0.07491313757543272), 0.0),
                ((15.411773016895275, 2.664567171964327, 0.07491313757543272), 0.0),
                ((15.91310568970497, 2.7021939887599644, 0.07491313757543272), 0.0),
                ((16.414438362514666, 2.7398208055556017, 0.07491313757543272), 0.0),
                ((16.91577103532436, 2.777447622351239, 0.07491313757543272), 0.0),
                ((17.417103708134057, 2.8150744391468763, 0.07491313757543272), 0.0),
                ((17.918436380943753, 2.852701255942514, 0.07491313757543272), 0.0),
                ((18.419769053753445, 2.890328072738151, 0.07491313757543272), 0.0),
                ((18.921101726563144, 2.9279548895337886, 0.07491313757543272), 0.0),
                ((19.42243439937284, 2.965581706329426, 0.07491313757543272), 0.0),
                ((19.923767072182535, 3.003208523125063, 0.07491313757543272), 0.0),
                ((20.42509974499223, 3.0408353399207004, 0.07491313757543272), 0.0),
                ((20.926432417801927, 3.0784621567163377, 0.07491313757543272), 0.0),
                ((21.427765090611622, 3.116088973511975, 0.07491313757543272), 0.0),
                ((21.92641067943828, 3.1777066741546727, 0.1847971581819653), 0.0),
                ((22.41349576278602, 3.30085617932413, 0.31048283411817923), 0.0),
                ((22.88130128351303, 3.4840928400137594, 0.4361685100543923), 0.0),
                ((23.322447092632714, 3.7245258954356304, 0.5618541859906058), 0.0),
                ((23.729973627566462, 4.018362248476311, 0.6875398619268193), 0.0),
                ((24.097451706933242, 4.3609663059949835, 0.8132255378630328), 0.0),
                ((24.419083957989738, 4.7469331104272925, 0.9389112137992461), 0.0),
                ((24.693484571891915, 5.176841593011522, 1.0665019086175291), 0.0),
                ((24.91095106144642, 5.638171546763291, 1.1940926034358121), 0.0),
                ((25.06794800597009, 6.123422986449974, 1.3216832982540951), 0.0),
                ((25.16192305707125, 6.624707027766175, 1.4492739930723784), 0.0),
                ((25.196118284431527, 7.13374772920208, 1.5280187951943522), 0.0),
                ((25.217943686481796, 7.6436436188626455, 1.5280187951943522), 0.0),
                ((25.23976908853206, 8.153539508523211, 1.5280187951943522), 0.0),
                ((25.261594490582326, 8.663435398183777, 1.5280187951943522), 0.0),
                ((25.283419892632594, 9.173331287844343, 1.5280187951943522), 0.0),
                ((25.30524529468286, 9.683227177504909, 1.5280187951943522), 0.0),
                ((25.327070696733124, 10.193123067165475, 1.5280187951943522), 0.0),
                ((25.348896098783392, 10.70301895682604, 1.5280187951943522), 0.0),
                ((25.370721500833657, 11.212914846486607, 1.5280187951943522), 0.0),
                ((25.392546902883925, 11.722810736147173, 1.5280187951943522), 0.0),
                ((25.41437230493419, 12.232706625807738, 1.5280187951943522), 0.0),
                ((25.436197706984455, 12.742602515468304, 1.5280187951943522), 0.0),
                ((25.458023109034723, 13.25249840512887, 1.5280187951943522), 0.0),
                ((25.479848511084988, 13.762394294789436, 1.5280187951943522), 0.0),
                ((25.501673913135257, 14.272290184450002, 1.5280187951943522), 0.0),
                ((25.52349931518552, 14.782186074110568, 1.5280187951943522), 0.0),
                ((25.545324717235786, 15.292081963771134, 1.5280187951943522), 0.0),
                ((25.567150119286055, 15.8019778534317, 1.5280187951943522), 0.0),
                ((25.58897552133632, 16.311873743092264, 1.5280187951943522), 0.0),
                ((25.610800923386588, 16.82176963275283, 1.5280187951943522), 0.0),
                ((25.632626325436853, 17.331665522413395, 1.5280187951943522), 0.0),
                ((25.654451727487118, 17.84156141207396, 1.5280187951943522), 0.0),
                ((25.676277129537386, 18.351457301734527, 1.5280187951943522), 0.0),
                ((25.69810253158765, 18.861353191395093, 1.5280187951943522), 0.0),
                ((25.71992793363792, 19.37124908105566, 1.5280187951943522), 0.0),
                ((25.741753335688184, 19.881144970716228, 1.5280187951943522), 0.0),
                ((25.76357873773845, 20.39104086037679, 1.5280187951943522), 0.0),
                ((25.785404139788717, 20.90093675003736, 1.5280187951943522), 0.0),
                ((25.807229541838982, 21.410832639697922, 1.5280187951943522), 0.0),
                ((25.829054943889247, 21.92072852935849, 1.5280187951943522), 0.0),
                ((25.850880345939515, 22.430624419019058, 1.5280187951943522), 0.0),
                ((25.87270574798978, 22.940520308679623, 1.5280187951943522), 0.0),
                ((25.89453115004005, 23.45041619834019, 1.5280187951943522), 0.0),
                ((25.916356552090313, 23.96031208800075, 1.5280187951943522), 0.0),
                ((25.938181954140582, 24.470207977661325, 1.5280187951943522), 0.0),
                ((25.960007356190847, 24.980103867321887, 1.5280187951943522), 0.0),
                ((25.98183275824111, 25.489999756982453, 1.5280187951943522), 0.0),
                ((26.0, 26.0, 1.5707963267948966), 0.0),
            ]
        )
    }

```

#### PDDL domain

```lisp
(define (domain robot_domain)
 (:requirements :strips :typing)
 (:types robot robot_config)
 (:predicates 
             (robot_at ?robot - robot ?configuration - robot_config)
 )
 (:action move
  :parameters ( ?robot - robot ?c_from - robot_config ?c_to - robot_config)
  :precondition (and (robot_at ?robot ?c_from))
  :effect (and (not (robot_at ?robot ?c_from)) (robot_at ?robot ?c_to)))
)
```

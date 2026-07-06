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
  :precondition (and
    (is_at ?l_from)
    (is_connected ?l_from ?l_to)
  )
  :effect (and
    (not (is_at ?l_from))
    (is_at ?l_to)
    (increase (total_travel_time) (travel_time ?l_from ?l_to))
  )
 )
)

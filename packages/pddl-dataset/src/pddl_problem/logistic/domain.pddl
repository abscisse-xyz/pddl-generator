(define (domain logistic_domain)
 (:requirements :strips :typing :negative-preconditions :durative-actions :numeric-fluents)
 (:types robot location package)
 (:predicates
   (robot_at ?robot - robot ?position - location)
   (robot_free ?robot - robot)
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
    (at start (is_connected ?l_from ?l_to))
    (over all (is_connected ?l_from ?l_to))
  )
  :effect (and
    (at start (not (robot_at ?robot ?l_from)))
    (at end (robot_at ?robot ?l_to))
  )
 )
 (:action load
  :parameters ( ?package - package ?robot - robot ?position - location)
  :precondition (and
    (robot_free ?robot)
    (package_at ?package ?position)
    (robot_at ?robot ?position)
  )
  :effect (and
    (not (robot_free ?robot))
    (not (package_at ?package ?position))
    (package_loaded ?package ?robot)
  )
 )
 (:action unload
  :parameters ( ?package - package ?robot - robot ?position - location)
  :precondition (and
    (package_loaded ?package ?robot)
    (robot_at ?robot ?position)
  )
  :effect (and
    (not (package_loaded ?package ?robot))
    (package_at ?package ?position)
    (robot_free ?robot)
  )
 )
)

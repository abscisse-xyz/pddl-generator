;; Enrico Scala (enricos83@gmail.com) and Miquel Ramirez (miquel.ramirez@gmail.com)
; Reference Paper: Scala, Enrico, Patrik Haslum, Sylvie Thiébaux, and Miquel Ramirez.
;                  "Subgoaling techniques for satisficing and optimal numeric planning."
;                  Journal of Artificial Intelligence Research 68 (2020): 691-752.
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; The Sailing domain models a number of sailing boats
; whose task is to rescue people in an unbounded area of the ocean.
; The positions of the boat and people to be rescued are described by their 2D coordinates.
; The model tries to take into account the different speeds that can be obtained in a sailing boat.
; Going upwind or fully downwind is slower. We assume that wind comes from the north.

(define (domain sailing)
     (:requirements :typing :durative-actions :numeric-fluents :negative-preconditions)
     (:types boat - object person - object)
     (:predicates
          (saved ?t - person)
          (idle ?b - boat)
          (still_alive)
          (started)
     )
     (:functions
          (x ?b - boat)
          (y ?b - boat)
          (d ?t - person)
          (deadline)
     )
     (:durative-action go_north_east
          :parameters (?b - boat)
          :duration (= ?duration 1)
          :condition (and
               (at start (and (idle ?b) (started)))
          )
          :effect (and
               (at start (not (idle ?b)))
               (at end (and (idle ?b) (increase (x ?b) 3) (increase (y ?b) 3)))
          )
     )
     (:durative-action go_north_west
          :parameters (?b - boat)
          :duration (= ?duration 1)
          :condition (and
               (at start (and (idle ?b) (started)))
          )
          :effect (and
               (at start (not (idle ?b)))
               (at end (and (idle ?b) (decrease (x ?b) 3) (increase (y ?b) 3)))
          )
     )
     (:durative-action go_est
          :parameters (?b - boat)
          :duration (= ?duration 1)
          :condition (and
               (at start (and (idle ?b) (started)))
          )
          :effect (and
               (at start (not (idle ?b)))
               (at end (and (idle ?b) (increase (x ?b) 6)))
          )
     )
     (:durative-action go_west
          :parameters (?b - boat)
          :duration (= ?duration 1)
          :condition (and
               (at start (and (idle ?b) (started)))
          )
          :effect (and
               (at start (not (idle ?b)))
               (at end (and (idle ?b) (decrease (x ?b) 6)))
          )
     )
     (:durative-action go_south_west
          :parameters(?b - boat)
          :duration (= ?duration 1)
          :condition (and
               (at start (and (idle ?b) (started)))
          )
          :effect (and
               (at start (not (idle ?b)))
               (at end (and (idle ?b) (increase (x ?b) 4) (decrease (y ?b) 4)))
          )
     )
     (:durative-action go_south_east
          :parameters(?b - boat)
          :duration (= ?duration 1)
          :condition (and
               (at start (and (idle ?b) (started)))
          )
          :effect (and
               (at start (not (idle ?b)))
               (at end (and (idle ?b) (decrease (x ?b) 4) (decrease (y ?b) 4)))
          )
     )
     (:durative-action go_south
          :parameters(?b - boat)
          :duration (= ?duration 1)
          :condition (and
               (at start (and (idle ?b) (started)))
          )
          :effect (and
               (at start (not (idle ?b)))
               (at end (and (idle ?b) (decrease (y ?b) 4)))
          )
     )
     (:durative-action save_person
          :parameters(?b - boat ?t - person)
          :duration (= ?duration 1)
          :condition (and
               (at start (and
                    (started)
                    (still_alive)
                    (idle ?b)
                    (>= (+ (x ?b) (y ?b)) (d ?t))
                    (>= (- (y ?b) (x ?b)) (d ?t))
                    (<= (+ (x ?b) (y ?b)) (+ (d ?t) 50))
                    (<= (- (y ?b) (x ?b)) (+ (d ?t) 50))))
               (at end (and (still_alive)))
          )
          :effect (and
               (at start (not (idle ?b)))
               (at end (and (saved ?t) (idle ?b)))
          )
     )
     (:durative-action overall
         :parameters ()
         :duration (= ?duration (deadline))
         :condition (and
             (at start (and (not (started))
             ))
         )
         :effect (and
             (at start (and (started)
             ))
             (at end (and (not (still_alive))
             ))
         )
     )

)

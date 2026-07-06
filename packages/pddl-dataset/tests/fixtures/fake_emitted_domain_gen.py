#!/usr/bin/env python3
"""Stand-in for an emitted-domain generator (openstacks). Writes BOTH a fresh
domain.pddl (in cwd) and the problem (via -problem_file)."""

import os
import sys

args = sys.argv[1:]
problem_file = None
for i, a in enumerate(args):
    if a == "-problem_file":
        problem_file = args[i + 1]
        break

if not problem_file:
    sys.exit("missing -problem_file")

with open(os.path.join(os.getcwd(), "domain.pddl"), "w") as fh:
    fh.write("(define (domain emitted))\n")

with open(problem_file, "w") as fh:
    fh.write("(define (problem emitted-instance))\n")

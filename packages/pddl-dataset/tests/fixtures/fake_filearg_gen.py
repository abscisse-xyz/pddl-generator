#!/usr/bin/env python3
"""Stand-in for a file-arg generator (cavediving). Writes problem to the path
given via -problem_file."""

import sys

args = sys.argv[1:]
problem_file = None
for i, a in enumerate(args):
    if a == "-problem_file":
        problem_file = args[i + 1]
        break

if not problem_file:
    sys.exit("missing -problem_file")

with open(problem_file, "w") as fh:
    fh.write("(define (problem fake)\n")
    fh.write(f"  ;; argv = {args}\n")
    fh.write(")\n")

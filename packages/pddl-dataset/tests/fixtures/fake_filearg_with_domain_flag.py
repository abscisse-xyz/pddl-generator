#!/usr/bin/env python3
"""Stand-in for travel/logistic-style generators: writes BOTH a domain file
(via -domain_file) and a problem file (via -problem_file) to the paths it
receives — never to its cwd."""

import sys

args = sys.argv[1:]
domain_file = problem_file = None
for i, a in enumerate(args):
    if a == "-domain_file":
        domain_file = args[i + 1]
    elif a == "-problem_file":
        problem_file = args[i + 1]

if not domain_file or not problem_file:
    sys.exit("missing -domain_file or -problem_file")

with open(domain_file, "w") as fh:
    fh.write("(define (domain emitted_via_flag))\n")
with open(problem_file, "w") as fh:
    fh.write(f"(define (problem fake) ;; argv = {args})\n")

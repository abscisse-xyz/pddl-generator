#!/usr/bin/env python3
"""Stand-in for a stdout-style generator (gripper, blocksworld, ...).

Echoes the argv it received as a fake PDDL problem so the runner test can verify
both file output and the captured command line.
"""

import sys

print("(define (problem fake)")
print(f"  ;; argv = {sys.argv[1:]}")
print(")")

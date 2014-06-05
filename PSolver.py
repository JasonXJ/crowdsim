#!/usr/bin/env python3

import crowdsim

g = crowdsim.generator.SimpleGenerator(10, 2, 0)
s = crowdsim.solver.PSolver(10, lambda x: 0.8, duplicate = 3)

s.link(g)
for x in s:
    print(x)

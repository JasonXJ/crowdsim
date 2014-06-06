#!/usr/bin/env python3

from crowdsim.generator import GeneralGenerator
import random

def printg(g):
    for x in g:
        print(x)
    print()

g = GeneralGenerator(10,2)
printg(g)

g2 = GeneralGenerator(10, range(2,12), range(1,11))
printg(g2)

l = []
for x in range(10):
    c = random.randrange(2,5)
    t = random.randrange(c)
    l.append((c,t))

g3 = GeneralGenerator(10, lambda x: l[x][0], lambda x: l[x][1])
g3.cacheAll()
for x in g3.cache:
    print(x)

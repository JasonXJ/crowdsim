#!/usr/bin/env python3

import crowdsim

g = crowdsim.generator.GeneralGenerator(10, 2, 0)
s = crowdsim.solver.PSolver(10, lambda x: 0.8, duplicate = 3)
d = crowdsim.deducer.MajorityVote()

crowdsim.linkAll(g, s, d)

d.cacheAll()

print('========== Answers ==========')
for x in s.cache:
    print(x)
print('=============================')

print('Accuracy:', crowdsim.evaluate(g.cache, d.cache, strict = True))

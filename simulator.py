#!/usr/bin/env python3

import crowdsim
import operator

g = crowdsim.generator.GeneralGenerator(10, 2, 1)
#s = crowdsim.solver.PSolver(10, lambda x: 0.8, duplicate = 3)
a = crowdsim.assigner.SimpleAssigner(3)
w = crowdsim.worker.PWorker(10, lambda x: 0.8)
d = crowdsim.deducer.MajorityVote()

crowdsim.linkAll(g, a, w, d)

print('========== Answers ==========')
for x in sorted(w, key = lambda x: x.task.id):
    print(x)
print('=============================')

print('Accuracy:', crowdsim.evaluate(d, strict = True))


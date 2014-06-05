#!/usr/bin/env python3
from .common import *

class BaseDeducer:
    pass

class MajorityVote(BaseDeducer):
    def __init__(cache = True):
        # actually, MajorityVote always caches in spite of the parameter
        pass
    def cacheAll(self):
        pass
    def link(self, generator, solver):
        self.taskDict = {}
        for a in solver:
            if a.taskID not in self.taskDict:
                self.taskDict[a.taskID] = [0 for x in range(generator.getOptionCount(a.taskID))]
            self.taskDict[a.taskID][a.label] += 1
        self.cache = []
        for ID in sorted(self.taskDict.keys()):
            mValue = -1
            for c, v in enumerate(self.taskDict[ID]):
                if v > mValue:
                    mValue = v
                    mChoice = c
            self.cache.append(SimpleAnswer(ID, mChoice))
    def __iter__(self):
        return iter(self.cache)

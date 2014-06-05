#!/usr/bin/env python3
from .common import *

class MajorityVote:
    def link(self, generator, solver):
        self.taskDict = {}
        for a in solver:
            if a.taskID not in self.taskDict:
                self.taskDict[a.taskID] = [0 for x in range(generator.getOptionCount(a.taskID))]
            self.taskDict[a.taskID][a.choice] += 1
        self.deducedAnswers = []
        for ID in sorted(self.taskDict.keys()):
            mValue = -1
            for c, v in enumerate(self.taskDict[ID]):
                if v > mValue:
                    mValue = v
                    mChoice = c
            self.deducedAnswers.append(SimpleAnswer(ID, mChoice))
    def __iter__(self):
        return iter(self.deducedAnswers)

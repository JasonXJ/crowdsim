#!/usr/bin/env python3
from .common import *

class BaseDeducer:
    pass

class MajorityVote(BaseDeducer):
    def link(self, generator, solver):
        self.generator = generator
        self.solver = solver
        self.taskDict = {}
        for a in solver:
            if a.taskId not in self.taskDict:
                self.taskDict[a.taskId] = [0 for x in range(generator.id_to_task[a.taskId].labelCount)]
            self.taskDict[a.taskId][a.label] += 1
        self.answerList = []
        for taskId in self.taskDict.keys():
            self.answerList.append(SimpleAnswer(taskId, maxIndex(self.taskDict[taskId])))
    def __iter__(self):
        return iter(self.answerList)

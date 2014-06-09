#!/usr/bin/env python3
from .common import *

class BaseDeducer:
    pass

class MajorityVote(BaseDeducer):
    def link(self, worker):
        self.worker = worker
        self.taskDict = {}
        for a in worker:
            if a.task not in self.taskDict:
                self.taskDict[a.task] = [0 for x in range(a.task.labelCount)]
            self.taskDict[a.task][a.label] += 1
        self.answerList = []
        for task in self.taskDict.keys():
            self.answerList.append(SimpleAnswer(task, maxIndex(self.taskDict[task])))
    def __iter__(self):
        return iter(self.answerList)

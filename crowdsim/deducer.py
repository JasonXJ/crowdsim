#!/usr/bin/env python3
from .common import *

class BaseDeducer:
    pass

class MajorityVote(BaseDeducer):
    def link(self, workerPool):
        self.workerPool = workerPool
        self.taskDict = {}
        for a in workerPool:
            if a.task not in self.taskDict:
                self.taskDict[a.task] = [0 for x in range(a.task.labelCount)]
            self.taskDict[a.task][a.label] += 1
        self.answerList = []
        for task in self.taskDict.keys():
            self.answerList.append(SimpleAnswer(task, maxIndex(self.taskDict[task])))
    def __iter__(self):
        return iter(self.answerList)

class passer(BaseDeducer):
    """This deducer do nothing but pass the results directly. It is used when
    we do not need to deduce answers from workerpool or the assigner do the
    deducing work by itself."""
    def __init__(self, source = 'worker'):
        """source can be "worker" or "deducer" """
        self.source = source
        if source not in ['worker', 'deducer']:
            raise ValueError('Unsupported source value ("{}")'.format(source))

    def link(self, workerPool):
        self.workerPool = workerPool
        if self.source == 'worker':
            self.answerList = workerPool.answerList
        else:
            self.answerList = workerPool.assigner.answerList
    def __iter__(self):
        return iter(self.answerList)

# put this import last
from .deducer_EM import *

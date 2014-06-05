#!/usr/bin/env python3
import random, bisect
from .common import *

class BaseSolver:
    pass

class PSolver(BaseSolver):
    """Solve tasks by choosing a random worker and assigning answer based on his accuracy"""
    def __init__(self, workerCount, accuracyFunc, assignWeights=None, duplicate=1, cache = True):
        """Init...

        Parameter:
            accuracyFunc: accuracyFunc should be function accept the worker ID and return accuracy.
            assignWeights: None if weights are equal or a iterable cantaining the integer weights for all workers.
        """
        self.workerCount = workerCount
        self.accuracyFunc = accuracyFunc
        self.duplicate = duplicate
        if cache:
            self.cache = []
            self.cacheAll = self._cacheAll
        else:
            self.cache = None
        if assignWeights is None:
            self.randomWorker = self.randomWorkerDirectly
            self.searchRange = workerCount
        else:
            self.randomWorker = self.randomWorkerWithWeight
            # see randomWorkerWithWeight() for the explaination of workerRange
            it = iter(assignWeights)
            self.workerRange = [next(it)]
            try:
                while True:
                    self.workerRange.append(self.workerRange[-1] + next(it))
            except StopIteration:
                pass
            self.searchRange = self.workerRange[-1]
    def _cacheAll(self):
        for x in self:
            pass
    def link(self, g):
        self.lIter = iter(g)
        self.duplicateIndex = self.duplicate
    def __iter__(self):
        return self
    def __next__(self):
        if self.duplicateIndex == self.duplicate:
            self.duplicateIndex = 0
            self.ongoingTask = next(self.lIter)
            self.usedWorker = []
        self.duplicateIndex += 1
        workerID = self.randomWorker()
        while workerID in self.usedWorker:
            # XXX rerun randomWorker() may be a problem if "workercount >> duplicate" is not satisfied
            workerID = self.randomWorker()
        self.usedWorker.append(workerID)
        if random.random() > self.accuracyFunc(workerID): # wrong answer
            label = random.randrange(self.ongoingTask.labelCount - 1)
            if label == self.ongoingTask.trueLabel:
                label = self.ongoingTask.labelCount - 1
        else: # right answer
            label = self.ongoingTask.trueLabel
        a = Answer(workerID, self.ongoingTask.ID, label)
        if self.cache is not None:
            self.cache.append(a)
        return a
    def randomWorkerDirectly(self):
        return random.randrange(self.searchRange)
    def randomWorkerWithWeight(self):
        # Given a random number x, if workerRange[i-1] <= x < workerRange[i], then return i
        return bisect.bisect_right(self.workerRange, random.randrange(self.searchRange))

#!/usr/bin/env python3
import random, bisect
from .common import *

class BaseSolver:
    pass

class PSolver(BaseSolver):
    """Solve tasks by choosing a random worker and assigning answer based on his accuracy"""
    def __init__(self, workerCount, accuracyFunc, assignWeights=None, duplicate=1):
        """Init...

        Parameter:
            accuracyFunc: accuracyFunc should be function accept the worker ID and return accuracy.
            assignWeights: None if weights are equal or a iterable cantaining the integer weights for all workers.
        """
        self.workerCount = workerCount
        self.accuracyFunc = accuracyFunc
        self.duplicate = duplicate
        if assignWeights is None:
            self.randomWorkerGenerator = self.randomWorkerDirectly
        else:
            self.randomWorkerGenerator = WeightedRandom(assignWeights)

    def link(self, g):
        self.generator = g
        self.answerList = []
        for task in g:
            usedWorker = []
            for dIndex in range(self.duplicate):
                workerId = self.randomWorkerGenerator()
                while workerId in usedWorker:
                    # XXX rerun randomWorkerGenerator() may be a problem if "workercount >> duplicate" is not satisfied
                    workerId = self.randomWorkerGenerator()
                usedWorker.append(workerId)
                if random.random() > self.accuracyFunc(workerId): # wrong answer
                    label = random.randrange(task.labelCount - 1)
                    if label == task.trueLabel:
                        label = task.labelCount - 1
                else: # right answer
                    label = task.trueLabel
                a = Answer(workerId, task.id, label)
                self.answerList.append(a)

    def __iter__(self):
        return iter(self.answerList)

    def randomWorkerDirectly(self):
        return random.randrange(self.workerCount)

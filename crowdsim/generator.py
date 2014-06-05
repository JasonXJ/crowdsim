#!/usr/bin/env python3
import random
from .common import *

class BaseGenerator:
    pass

class GeneralGenerator(BaseGenerator):
    """Class to generate some SimpleHIT """
    def __init__(self, taskCount, labelCount, trueLabel=None, cache = True):
        """Init...

        Parameter:
            taskCount: number of task to generate
            labelCount: can be a callable/iterable object or just an int
            trueLabel: Can be None, callable/iterable object or int. If is None, the trueOptions are assigned randomly.
        """
        self.taskCount = taskCount
        self.optionCountGenerator = toCallable(labelCount)
        if trueLabel is None:
            self.trueOptionGenerator = self.defaultTrueOptionGenerator
        else:
            self.trueOptionGenerator = toCallable(trueLabel)

        if cache:
            self.cache = []
            self.cacheAll = self._cacheAll
        else:
            self.cache = None

        self.ongoingTaskID = 0

    def defaultTrueOptionGenerator(self, x):
        return random.randrange(self.ongoingOptionCount)

    def _cacheAll(self):
        for x in self:
            pass

    def __iter__(self):
        return self

    def __next__(self):
        if self.ongoingTaskID < self.taskCount:
            self.ongoingOptionCount = self.optionCountGenerator(self.ongoingTaskID) # for defaultTrueOptionGenerator()
            task = SimpleTask(self.ongoingTaskID, self.ongoingOptionCount, self.trueOptionGenerator(self.ongoingTaskID))
            self.ongoingTaskID += 1
            if self.cache is not None:
                self.cache.append(task)
            return task
        else:
            raise StopIteration
    def getOptionCount(self, taskID):
        return self.cache[taskID].labelCount
    def getTrueOption(self, taskID):
        return self.cache[taskID].trueLabel

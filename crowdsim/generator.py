#!/usr/bin/env python3
import random
from .common import *

class SimpleGenerator:
    """Class to generate some SimpleHIT """
    def __init__(self, taskCount, optionCount, trueOption=None):
        """Init...

        Parameter:
            taskCount: number of task to generate
            optionCount: can be a callable/iterable object or just an int
            trueOption: Can be None, callable/iterable object or int. If is None, the trueOptions are assigned randomly.
        """
        self.taskCount = taskCount
        self.optionCountGenerator = toCallable(optionCount)
        if trueOption is None:
            self.trueOptionGenerator = self.defaultTrueOptionGenerator
        else:
            self.trueOptionGenerator = toCallable(trueOption)
        self.ongoingTaskID = 0

    def defaultTrueOptionGenerator(self, x):
        return random.randrange(self.ongoingOptionCount)

    def __iter__(self):
        return self

    def __next__(self):
        if self.ongoingTaskID < self.taskCount:
            self.ongoingOptionCount = self.optionCountGenerator(self)
            task = SimpleTask(self.ongoingTaskID, self.ongoingOptionCount, self.trueOptionGenerator(self))
            self.ongoingTaskID += 1
            return task
        else:
            raise StopIteration

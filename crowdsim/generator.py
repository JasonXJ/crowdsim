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

        self.taskList = []
        for taskID in range(self.taskCount):
            self.ongoingOptionCount = self.optionCountGenerator(taskID) # for defaultTrueOptionGenerator()
            self.taskList.append(SimpleTask(taskID, self.ongoingOptionCount, self.trueOptionGenerator(taskID)))

    def defaultTrueOptionGenerator(self, x):
        return random.randrange(self.ongoingOptionCount)

    def __iter__(self):
        return iter(self.taskList)
    
    def getOptionCount(self, taskID):
        return self.taskList[taskID].optionCount
    def getTrueOption(self, taskID):
        return self.taskList[taskID].trueOption

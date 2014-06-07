#!/usr/bin/env python3
import random
from .common import *

class BaseGenerator:
    pass

class GeneralGenerator(BaseGenerator):
    """Class to generate some SimpleHIT """
    def __init__(self, taskCount, labelCount, trueLabel=None):
        """Init...

        Parameter:
            taskCount: number of task to generate
            labelCount: can be a callable/iterable object or just an int
            trueLabel: Can be None, callable/iterable object or int. If is None, the trueLabels are assigned randomly.
        """
        self.taskCount = taskCount
        self.labelCountGenerator = toCallable(labelCount)
        if trueLabel is None:
            self.trueLabelGenerator = self.defaultTrueLabelGenerator
        else:
            self.trueLabelGenerator = toCallable(trueLabel)

        self.id_to_task = []
        self.taskList = self.id_to_task
        for self.ongoingTaskId in range(self.taskCount):
            self.ongoingLabelCount = self.labelCountGenerator(self.ongoingTaskId) # for defaultTrueLabelGenerator()
            task = SimpleTask(self.ongoingTaskId, self.ongoingLabelCount, self.trueLabelGenerator(self.ongoingTaskId))
            self.id_to_task.append(task)

    def defaultTrueLabelGenerator(self, x):
        return random.randrange(self.ongoingLabelCount)

    def __iter__(self):
        return iter(self.id_to_task)

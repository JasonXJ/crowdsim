#!/usr/bin/env python3
from collections import namedtuple

SimpleTask = namedtuple('SimpleTask', 'id, labelCount, trueLabel')
Answer = namedtuple('Answer', 'workerId, task, label')
SimpleAnswer = namedtuple('SimpleAnswer', 'task, label')
SimpleAnswerWithLabelCount = namedtuple('SimpleAnswerWithLableCount', 'task, label, yesCount, noCount')
BinaryTaskMetrics = namedtuple('BinaryTaskMetrics', 'precision, recall, f1, accuracy')

def toCallable(obj):
    try:
        i = iter(obj)
    except TypeError:
        # not iterable
        pass
    else:
        return lambda x: next(i)
    if callable(obj):
        return obj
    return lambda x: obj

import random, bisect
class WeightedRandom:
    """Return a random integer based on the weights"""
    def __init__(self, weights):
        """Init...

        weights should be iterable.
        """

        it = iter(weights)
        rangeList = [next(it)]
        try:
            while True:
                rangeList.append(next(it) + rangeList[-1])
        except StopIteration:
            pass
        self.rangeList = rangeList
        self.searchRange = rangeList[-1]
    def __call__(self):
        # Generate a random number x in range [0, self.search range], if
        # workerRange[i-1] < x <= workerRange[i], then return i

        # !! Do not use bisect_right() because random.uniform(0, b) may return
        # b, in this case bisect_right() will return `len(self.rangeList)`!
        return bisect.bisect_left(self.rangeList, random.uniform(0, self.searchRange))

def maxIndex(l):
    mi = 0
    mv = l[0]
    for i, v in enumerate(l):
        if v > mv:
            mv = v
            mi = i
    return mi

# Exceptions
class FailToGetStrategy(Exception):
    pass
class GeneratorNotCompatible(Exception):
    pass
class StrategyStopAtOrigin(Exception):
    pass
class RunOutOfActiveTask(Exception):
    # there is no active task currently, but there are still some inactive
    # tasks
    pass
class RunOutOfAllTask(Exception):
    # there is no task at all
    pass

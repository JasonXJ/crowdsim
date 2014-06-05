#!/usr/bin/env python3
from collections import namedtuple

SimpleTask = namedtuple('SimpleTask', 'ID, optionCount, trueOption')
Answer = namedtuple('Answer', 'wokerID, taskID, choice')

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

#!/usr/bin/env python3

from . import common, generator, solver, deducer, assigner, worker

def evaluate(answers, strict = False):
    """evaluate the answers

    if strict == True, will raise ValueError if there are duplicated answers.
    """

    if strict:
        taskSet = set()
        for a in answers:
            if a.task.id in taskSet:
                raise ValueError('Duplicated answers')
            taskSet.add(a.task.id)
        del taskSet

    count = 0
    totalCount = 0
    for a in answers:
        totalCount += 1
        if a.label == a.task.trueLabel:
            count += 1
    return count / totalCount

def linkAll(generator = None, assigner = None, worker = None, deducer = None):
    if assigner:
        assigner.link(generator)
    if worker:
        worker.link(assigner)
    if deducer:
        deducer.link(worker)

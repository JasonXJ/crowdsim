#!/usr/bin/env python3

from . import common, generator, solver, deducer, assigner, worker

def evaluate(tasks, answers, strict = False):
    """evaluate the answers

    if strict == True, will raise ValueError if there are duplicated tasks or
    each task does not have exactly one answer
    """

    if strict:
        taskSet = set()
        for t in tasks:
            if t.id in taskSet:
                raise ValueError('Duplicated tasks')
            taskSet.add(t.id)
        errString = 'tasks and answers do not match'
        for a in answers:
            if a.taskId not in taskSet:
                raise ValueError(errString)
            taskSet.remove(a.taskId)
        if len(taskSet) != 0:
            raise ValueError(errString)

    taskDict = {t.id : t.trueLabel for t in tasks}
    count = 0
    for a in answers:
        if a.label == taskDict[a.taskId]:
            count += 1
    return count / len(answers)

def linkAll(generator = None, solver = None, deducer = None):
    if solver:
        solver.link(generator)
    if deducer:
        deducer.link(generator, solver)

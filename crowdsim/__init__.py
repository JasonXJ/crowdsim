#!/usr/bin/env python3

from . import common, generator, deducer, assigner, workerpool


def linkAll(generator = None, assigner = None, workerPool = None, deducer = None):
    if assigner:
        assigner.link(generator)
    if workerPool:
        workerPool.link(assigner)
    if deducer:
        deducer.link(workerPool)

def hasDuplicatedAnswers(answers):
    taskSet = set()
    for a in answers:
        if a.task.id in taskSet:
            return True
        taskSet.add(a.task.id)
    return False

def evaluate(answers, detectDuplicate = False):
    """evaluate the answers and return accuracy"""

    if detectDuplicate and hasDuplicatedAnswers(answers):
        raise ValueError('Duplicated answers')

    count = 0
    totalCount = 0
    for a in answers:
        totalCount += 1
        if a.label == a.task.trueLabel:
            count += 1
    return count / totalCount

def getConfusionMatrix(answers, detectDuplicate = False):
    """evaluate the answers and return confusion matrix
    
    All tasks should have the same label counts. The return confusion matrix's
    structure is: confusionMatrix[actual_label][predict_label]
    """
    if detectDuplicate and hasDuplicatedAnswers(answers):
        raise ValueError('Duplicated answers')

    # confusionMatrix[actual_label][predict_label]
    it = iter(answers)
    a = next(it)
    labelCount = a.task.labelCount
    confusionMatrix = [ [0 for i in range(labelCount)] for j in range(labelCount)]
    confusionMatrix[a.task.trueLabel][a.label] += 1
    while True:
        try:
            a = next(it)
        except StopIteration:
            break
        else:
            confusionMatrix[a.task.trueLabel][a.label] += 1
    return confusionMatrix


def getBinaryTaskMetrics(confusionMatrix):
    assert(len(confusionMatrix) == 2)
    precision = confusionMatrix[1][1] / (confusionMatrix[1][1] + confusionMatrix[0][1])
    recall = confusionMatrix[1][1] / (confusionMatrix[1][1] + confusionMatrix[1][0])
    f1 = 2*precision*recall / (precision + recall)
    accuracy = (confusionMatrix[0][0] + confusionMatrix[1][1]) / (confusionMatrix[0][0] + confusionMatrix[0][1] + confusionMatrix[1][0] + confusionMatrix[1][1])
    return common.BinaryTaskMetrics(precision, recall, f1, accuracy)

import random
from .common import *

def solveTask(task, workerAccuracy):
    if random.random() > workerAccuracy: # wrong answer
        label = random.randrange(task.labelCount - 1)
        if label == task.trueLabel:
            label = task.labelCount - 1
    else: # right answer
        label = task.trueLabel
    return label
def solveTask2(task, pFalsePositive, pFalseNegative):
    assert(task.labelCount == 2)
    if task.trueLabel == 0:
        p = pFalsePositive
    else:
        p = pFalseNegative
    if random.random() > p:
        return task.trueLabel
    else:
        return 1 - task.trueLabel

class BaseWorkerPool:
    pass

class PWorkerPool(BaseWorkerPool):
    def __init__(self, workerCount, accuracyFunc, assignWeights=None):
        """Init...

        Parameter:
            accuracyFunc: accuracyFunc should be function accept the worker ID and return accuracy.
            assignWeights: None if weights are equal or a iterable cantaining the integer weights for all workers.
        """
        self.workerCount = workerCount
        self.accuracyFunc = accuracyFunc
        self.cost = 0
        if assignWeights is None:
            self.randomWorkerGenerator = self.randomWorkerDirectly
        else:
            self.randomWorkerGenerator = WeightedRandom(assignWeights)
    def link(self, assigner):
        self.assigner = assigner
        self.answerList = []
        while True:
            workerId = self.randomWorkerGenerator()
            try:
                task = assigner.assign(workerId)
            except RunOutOfAllTask:
                break
            if task != None: # assigner may return None because no task for the particular worker
                answer = self._solve(task, workerId)
                self.answerList.append(Answer(workerId, task, answer))
                self.assigner.update(workerId, task, answer)
                self.cost += 1
    def __iter__(self):
        return iter(self.answerList)
    def randomWorkerDirectly(self):
        return random.randrange(self.workerCount)
    def _solve(self, task, workerId):
        return solveTask(task, self.accuracyFunc(workerId))

class PWorkerPool2(PWorkerPool):
    def __init__(self, workerCount, accuracyFunc, assignWeights = None):
        """Identical to PWorkerPool except the return values of accuracyFunc.
        
        accuracyFunc should return a tuple (false positive rate, false negetive rate)
        """
        PWorkerPool.__init__(self, workerCount, accuracyFunc, assignWeights)
    def _solve(self, task, workerId):
        return solveTask2(task, *self.accuracyFunc(workerId))

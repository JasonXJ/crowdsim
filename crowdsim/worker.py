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

class BaseWorker:
    pass

class PWorker(BaseWorker):
    def __init__(self, workerCount, accuracyFunc, assignWeights=None):
        """Init...

        Parameter:
            accuracyFunc: accuracyFunc should be function accept the worker ID and return accuracy.
            assignWeights: None if weights are equal or a iterable cantaining the integer weights for all workers.
        """
        self.workerCount = workerCount
        self.accuracyFunc = accuracyFunc
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
                task = assigner.get(workerId)
            except EOFError:
                break
            if task != None: # assigner may return None because no task for the particular worker
                self.answerList.append(Answer(workerId, task, solveTask(task, self.accuracyFunc(workerId))))
    def __iter__(self):
        return iter(self.answerList)
    def randomWorkerDirectly(self):
        return random.randrange(self.workerCount)

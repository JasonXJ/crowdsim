from .common import *
import collections

class BaseAssigner:
    pass

class AssignInfo:
    def __init__(self):
        self.unconfirmedWorkers = set()
        self.confirmedWorkers = set()
    def assign(self, worker):
        assert(worker not in self.confirmedWorkers and worker not in self.unconfirmedWorkers)
        self.unconfirmedWorkers.add(worker)
    def confirm(self, worker):
        self.unconfirmedWorkers.remove(worker) # will raise KeyError if worker does not exist
        self.confirmedWorkers.add(worker)
    def abandon(self, worker):
        self.unconfirmedWorkers.remove(worker)
    def __contains__(self, item):
        return item in self.unconfirmedWorkers or item in self.confirmedWorkers
    def __len__(self):
        return len(self.unconfirmedWorkers) + len(self.confirmedWorkers)
    def confirmedCount(self):
        return len(self.confirmedWorkers)

class SimpleAssigner(BaseAssigner):
    """Assign tasks and guarantee a worker never receive the same task twice."""
    def __init__(self, duplicate = 1):
        self.duplicate = duplicate
        pass
    def link(self, generator):
        self.generator = generator
        self.task_to_assignInfo = {task : AssignInfo() for task in generator}
        self.inactive_task_to_assignInfo = {}
    def assign(self, workerId):
        if len(self.task_to_assignInfo) == 0:
            if len(self.inactive_task_to_assignInfo) == 0:
                raise RunOutOfAllTask
            raise RunOutOfActiveTask
        else:
            for task, assignInfo in self.task_to_assignInfo.items():
                if workerId not in assignInfo:
                    break
            else:
                return None
            assignInfo.assign(workerId)
            if len(assignInfo) == self.duplicate:
                # inactive the task
                self.inactive_task_to_assignInfo[task] = assignInfo
                del self.task_to_assignInfo[task]
            return task
    def update(self, workerId, task, label):
        if task in self.task_to_assignInfo:
            self.task_to_assignInfo[task].confirm(workerId)
        else:
            self.inactive_task_to_assignInfo[task].confirm(workerId)
            if self.inactive_task_to_assignInfo[task].confirmedCount() == self.duplicate:
                del self.inactive_task_to_assignInfo[task]
    def abandon(self, workerId, task):
        if task in self.inactive_task_to_assignInfo:
            # reactive the task
            self.task_to_assignInfo[task] = self.inactive_task_to_assignInfo[task]
            del self.inactive_task_to_assignInfo[task]
        self.task_to_assignInfo[task].abandon(workerId)

from . import crowdscreen
# XXX cannot assign a task again until the answer is received.
class StrategyAssigner(BaseAssigner):
    def __init__(self, strategyGrid):
        self.strategyGrid = strategyGrid
        if self.strategyGrid[0][0] == crowdscreen.PASS or self.strategyGrid[0][0] == crowdscreen.FAIL:
            raise StrategyStopAtOrigin(self.strategyGrid[0][0])
    def link(self, generator):
        self.generator = generator
        self.activeTasks = set()
        self.task_to_assignInfo_ynCount = dict()
        for task in generator:
            if task.labelCount != 2:
                raise ValueError('Only support 2-label tasks')
            self.activeTasks.add(task)
            self.task_to_assignInfo_ynCount[task] = [AssignInfo(), 0, 0]
        self.answerList = [] # final answers
    def assign(self, workerId):
        if len(self.task_to_assignInfo_ynCount) == 0:
            raise RunOutOfAllTask
        elif len(self.activeTasks) == 0:
            raise RunOutOfActiveTask
        else:
            for task in self.activeTasks:
                assignInfo = self.task_to_assignInfo_ynCount[task][0]
                if workerId not in assignInfo:
                    break
            else:
                return None
            assignInfo.assign(workerId)
            self.activeTasks.remove(task) # not support assign a task again until the answer is received
            return task
    def update(self, workerId, task, label):
        assignInfo_yesCount_noCount = self.task_to_assignInfo_ynCount[task]
        assignInfo_yesCount_noCount[0].confirm(workerId)
        assignInfo_yesCount_noCount[2 - label] += 1
        yesCount = assignInfo_yesCount_noCount[1]
        noCount = assignInfo_yesCount_noCount[2]
        state = self.strategyGrid[noCount][yesCount] 
        if state == crowdscreen.PASS:
            self.answerList.append(SimpleAnswerWithLabelCount(task, 1, yesCount, noCount))
            del self.task_to_assignInfo_ynCount[task]
        elif state == crowdscreen.FAIL:
            self.answerList.append(SimpleAnswerWithLabelCount(task, 0, yesCount, noCount))
            del self.task_to_assignInfo_ynCount[task]
        else: # conn
            self.activeTasks.add(task)
    def abandon(self, workerId, task):
        self.task_to_assignInfo_ynCount[task][0].abandon(workerId)
        self.activeTasks.add(task)

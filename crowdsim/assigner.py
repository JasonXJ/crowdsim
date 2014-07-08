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

class SimpleAssigner2(BaseAssigner):
    def __init__(self, duplicate = 1):
        self.duplicate = duplicate
        pass
    def link(self, generator):
        self.generator = generator
        self.it = iter(generator)
    def assign2(self):
        try:
            task = next(self.it)
        except StopIteration:
            raise RunOutOfAllTask
        return AnonymousAssignment(task, self.duplicate)
    def update(self, workerId, task, label):
        pass



from . import crowdscreen
class BaseStrategyAssigner(BaseAssigner):
    def __init__(self, t = None, m = None, s = None, e0 = None, e1 = None, strategyGrid = None):
        '''If strategyGrid is given, other parameters are ignored'''
        if strategyGrid:
            self.strategyGrid = strategyGrid
        else:
            self.strategy = crowdscreen.getBestLadderStrategy(t, m, s, e0, e1)
            self.strategyGrid = self.strategy.grid()
        if self.strategyGrid[0][0] == crowdscreen.PASS or self.strategyGrid[0][0] == crowdscreen.FAIL:
            raise StrategyStopAtOrigin(self.strategyGrid[0][0])
        self.stepsToNearestTermPoint = crowdscreen.calcStepsToNearestTermPoint(strategyGrid)

    def link(self, generator):
        self.generator = generator
        self.answerList = [] # final answers

        self.activeTasks = set(generator)
        for task in self.activeTasks:
            if task.labelCount != 2:
                raise ValueError('Only support 2-label tasks')

class StrategyAssigner(BaseStrategyAssigner):
    def link(self, generator):
        BaseStrategyAssigner.link(self, generator)
        self.task_to_yes_no_assignInfo = {t : [0, 0, AssignInfo()] for t in self.activeTasks}

    def assign(self, workerId):
        if len(self.task_to_yes_no_assignInfo) == 0:
            raise RunOutOfAllTask
        elif len(self.activeTasks) == 0:
            raise RunOutOfActiveTask
        else:
            for task in self.activeTasks:
                assignInfo = self.task_to_yes_no_assignInfo[task][-1]
                if workerId not in assignInfo:
                    break
            else:
                return None
            assignInfo.assign(workerId)
            if not self.isActive(task):
                self.activeTasks.remove(task)
            return task

    def update(self, workerId, task, label):
        yes, no, assignInfo = self.task_to_yes_no_assignInfo[task]
        if label == 0:
            no += 1
        else:
            yes += 1

        state = self.strategyGrid[no][yes] 
        if state == crowdscreen.UNREACHABLE:
            raise ValueError("Reach UNREACHABLE node")
        if state == crowdscreen.PASS:
            self.answerList.append(SimpleAnswerWithLabelCount(task, 1, yes, no))
            del self.task_to_yes_no_assignInfo[task]
            assert(task not in self.activeTasks)
        elif state == crowdscreen.FAIL:
            self.answerList.append(SimpleAnswerWithLabelCount(task, 0, yes, no))
            del self.task_to_yes_no_assignInfo[task]
            assert(task not in self.activeTasks)
        else: # conn
            self.task_to_yes_no_assignInfo[task][0] = yes
            self.task_to_yes_no_assignInfo[task][1] = no
            assignInfo.confirm(workerId)
            if self.isActive(task):
                self.activeTasks.add(task)

    def abandon(self, workerId, task):
        self.task_to_yes_no_assignInfo[task][-1].abandon(workerId)
        self.activeTasks.add(task)

    def isActive(self, task):
        yes, no, assignInfo = self.task_to_yes_no_assignInfo[task]
        left = self.stepsToNearestTermPoint[no][yes] - len(assignInfo.unconfirmedWorkers)
        assert(left >= 0)
        return left > 0

class StrategyAssigner2(BaseStrategyAssigner):
    """An assigner use crowdscreen strategy and interface assign2()"""
    def link(self, generator):
        BaseStrategyAssigner.link(self, generator)
        # `..._yes_no_active` means the number of yes/no received and the number of
        # assignments that has not received answers respecially
        self.task_to_yes_no_active = { task: [0, 0, 0] for task in self.activeTasks }

    def assign2(self):
        if len(self.task_to_yes_no_active) == 0:
            raise RunOutOfAllTask
        else:
            while len(self.activeTasks) != 0:
                task = self.activeTasks.pop()
                times = self.timesCanAsk(task)
                assert(times >= 0)
                if times == 0:
                    continue
                self.task_to_yes_no_active[task][-1] += times
                return AnonymousAssignment(task, times)
            raise RunOutOfActiveTask

    def update(self, workerId, task, label):
        yes, no, active = self.task_to_yes_no_active[task]
        if active == 0:
            raise ValueError("This task (id={}) has no active assignment".format(task.id))
        active -= 1
        if label == 0:
            no += 1
        else:
            yes += 1
        state = self.strategyGrid[no][yes]
        if state == crowdscreen.UNREACHABLE:
            raise ValueError("Reach UNREACHABLE node")
        if state == crowdscreen.PASS:
            self.answerList.append(SimpleAnswerWithLabelCount(task, 1, yes, no))
            del self.task_to_yes_no_active[task]
            self.activeTasks.discard(task)
        elif state == crowdscreen.FAIL:
            self.answerList.append(SimpleAnswerWithLabelCount(task, 0, yes, no))
            del self.task_to_yes_no_active[task]
            self.activeTasks.discard(task)
        else: # conn
            self.task_to_yes_no_active[task] = [yes, no, active]
            if self.timesCanAsk(task) > 0:
                self.activeTasks.add(task)

    def timesCanAsk(self, task):
        yes, no, active = self.task_to_yes_no_active[task]
        steps = self.stepsToNearestTermPoint[no][yes]
        return steps - active

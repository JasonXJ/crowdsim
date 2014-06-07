class BaseAssigner:
    def runOutOfTask(self):
        raise EOFError

class SimpleAssigner(BaseAssigner):
    """Assign tasks and guarantee a worker never receive the same task twice."""
    def __init__(self, duplicate = 1):
        self.duplicate = duplicate
        pass
    def link(self, generator):
        self.task_to_workers = {task : [] for task in generator}
    def get(self, workerId):
        if len(self.task_to_workers) == 0:
            self.runOutOfTask()
        else:
            for task, workers in self.task_to_workers.items():
                if workerId not in workers:
                    break
            else:
                return None
            if len(workers) == self.duplicate - 1:
                del self.task_to_workers[task]
            else:
                workers.append(workerId)
            return task

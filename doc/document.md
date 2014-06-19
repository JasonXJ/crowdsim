# Overview
The simulator comprises 4 parts: generator, assigner, worker and deducer. There may be multiple classes that implement each part.

After definding the instances `g`, `a`, `w` and `d` for each part, we can link them by calling `crowdsim.linkall(g, a, w, d)`.
Alternatively, we can link them one by one:

```python
a.link(g)
w.link(a)
d.link(w)
```

All the classes of the 4 parts should implement `link(former_part_class_instance)` and store a reference to `former_part_class_instance`. For example, assigner `a` and worker `w` should store the reference to the varibles `self.generator` and `self.assigner` respectively.

# generator
Generators is used to generate tasks (standard task classes are defined in crowdsim/common.py).
All generators should be iterable (and this is the standard interface), so that task can be read from a generator by the following codes:

```python
for task in SomeGenerator:
    ...
```

All generators should be a subclass of `BaseGenerator`.

## `GeneralGenerator`
`GeneralGenerator` is a class of generator.

```python
class GeneralGenerator(BaseGenerator):
    """Class to generate some SimpleHIT"""
    def __init__(self, taskCount, labelCount, trueLabel=None):
        """Init...

        Parameter:
            taskCount: number of task to generate
            labelCount: can be a callable/iterable object or just an int
            trueLabel: Can be None, callable/iterable object or int. If is None, the trueLabels are assigned randomly.
        """
        ...
    ...
```

# Assigner
Assigners read the tasks from generator and assign tasks when workers requests.
All assigners should be a subclass of `BaseAssigner`

## Standard interface

### `def assign(self, workerId)`

The consequences of calling this function can be:
* Exception `RunOutOfAllTask` is raised: No more tasks can be assigned anymore. A worker should stop requesting from assigner.
* Exception `RunOutOfActiveTask` is raised: No more tasks can be assigned currently until the assigner receiving some feedback (see interface `update` and `abandon`). A worker should try again after giving some feedback.
* `None` is returned: No more tasks for the worker currently. A worker should try again after giving some feedback or call `assign` with another `workerId`
* A task is returned.

### `def update(self, workerId, task, label)`
A worker should call this function to tell assigner the answers whenever they are available.

### `def abandon(self, workerId, task)`
Instead of calling `update` to tell the assigner the answer, a worker can call `abandon` to return the task to assigner.

## Assigner Classes
* `SimpleAssigner` assigns each task `duplicate` times and guarantees a worker of the same `workerId` never receive the same task twice.
* `StrategyAssigner` assign task based on "strategy".

# Worker
A worker gets tasks from an assigner and solves them.
All workers classes should be an subclass of `BaseWorker` and should be iterable (this is the standard interface) so that answers can be read from a worker by the following codes:

```python
for answer from SomeWorker:
    ...
```

# Deducer
A deducer analyses answers from worker and tries to deduced the true answers.
All deducer should a subclass of `BaseDeducer` and should be iterable (this is the standard interface) so that the deduced answers can be read by the following codes:

```python
for answer from SomeDeducer:
    ...
```

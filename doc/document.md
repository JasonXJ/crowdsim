# Overview
The simulator comprises 4 part: generator, assigner, worker and deducer. There may be multiple classes that implement each part.

After definding the instances `g`, `a`, `w` and `d` for each part, we can link them by calling `crowdsim.linkall(g, a, w, d)`.
Alternatively, we can link them one by one:

```python
a.link(g)
w.link(a)
d.link(w)
```

# generator
Generator is used to generate tasks (standard task classes are defined in crowdsim/common.py).
All generator should be iterable, so that task can be read from a generator by the following codes:

```python
for task in SomeGenerator:
    ...
```

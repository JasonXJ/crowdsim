# Overview
The simulator comprises 4 part: generator, assigner, worker and deducer. There may be multiple classes that implement each part.

After definding the instances `g`, `a`, `w` and `d` for each part, we can link them by calling `crowdsim.linkall(g, a, w, d)`.

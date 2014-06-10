PASS = BLUE = 1
FAIL = RED = 2
CONN = GREEN = 0
UNREACHABLE = -1

def printGrid(grid):
    # print a grid where grid[X][Y] denote the value of point (x = X, y = Y)
    range_x = len(grid)
    range_y = len(grid[0])
    for y in range(range_y - 1, -1, -1):
        for x in range(0, range_x):
            print('{}'.format(grid[x][y]), end = '\t')
        print()
    print('0 -----> x')

class strategy:
    def __init__(self, m, s, e0, e1):
        self.m = m
        self.s = s
        self.e0 = e0
        self.e1 = e1
        self.grid = self._getGrid(UNREACHABLE)
        self.p0 = None
        self.p1 = None
        self.e = self.c = None
        self.eEach = None # store the e for each terminating node
    def calc(self):
        if not self.e or not self.c:
            self.checkGrid()
            self._calcP()
            self.e = self.c = 0
            self.eEach = {}
            for x in range(self.m + 1):
                for y in range(self.m + 1):
                    pReach = self.p0[x][y] + self.p1[x][y]
                    if self.grid[x][y] == PASS:
                        self.eEach[(x,y)] = self.p0[x][y] / pReach
                        self.e += self.p0[x][y]
                        self.c += (x + y) * pReach
                    elif self.grid[x][y] == FAIL:
                        self.eEach[(x,y)] = self.p1[x][y] / pReach
                        self.e += self.p1[x][y]
                        self.c += (x + y) * pReach

    def checkGrid(self):
        # check the grid and ensure unreachable nodes are labeled correctly.
        visitedGrid = self._getGrid(False)
        self._checkGrid_visit(0, 0, visitedGrid)
        for x in range(self.m + 1):
            for y in range(self.m + 1):
                if visitedGrid[x][y] == False:
                    self.grid[x][y] = UNREACHABLE

    def _checkGrid_visit(self, x, y, visitedGrid):
        if x + y > self.m:
            raise RuntimeError('The strategy violates the restriction of "m"')
        if visitedGrid[x][y] == True:
            return
        visitedGrid[x][y] = True
        gridValue = self.grid[x][y]
        if gridValue == UNREACHABLE:
            raise RuntimeError('Unexpected unreachable node')
        if gridValue == CONN: # continue
            self._checkGrid_visit(x + 1, y, visitedGrid)
            self._checkGrid_visit(x, y + 1, visitedGrid)


    def _getGrid(self, initValue = 0):
        return [ [initValue for i in range(self.m + 1)] for x in range(self.m + 1) ]
    def _calcP(self):
        if not self.p0 or not self.p1:
            self.p0 = self._getGrid()
            self.p1 = self._getGrid()
            for x in range(self.m + 1):
                for y in range(self.m + 1):
                    if x == y == 0:
                        self.p0[0][0] = 1 - self.s
                        self.p1[0][0] = self.s
                    else:
                        p0_l = p0_d = p1_l = p1_d = 0 # l -> left, d -> down
                        if x > 0 and self.grid[x - 1][y] == CONN:
                            p0_l = self.p0[x-1][y]
                            p1_l = self.p1[x-1][y]
                        if y > 0 and self.grid[x][y-1] == CONN:
                            p0_d = self.p0[x][y-1]
                            p1_d = self.p1[x][y-1]
                        self.p0[x][y] = p0_l*(1 - self.e0)+ p0_d*self.e0
                        self.p1[x][y] = p1_l*self.e1 + p1_d*(1-self.e1)

import itertools
class ladderGenerator:
    """This class iterates though all ladder start from y/x axis and ensures the last segment of the ladder is horizontal/vertical."""
    UPPER_LADDER = 0
    LOWER_LADDER = 1
    def __init__(self, m, ladderType):
        self.m = m
        self.isUpperLadder = False
        if ladderType == self.UPPER_LADDER:
            self.isUpperLadder = True

    def reset(self, startPoint, decisionPoint):
        self.x = startPoint[0]
        self.y = startPoint[1]
        self.dx = decisionPoint[0]
        self.dy = decisionPoint[1]

        delta_x = self.dx - self.x
        delta_y = self.dy - self.y

        if self.isUpperLadder:
            assert(self.x == 0)
            delta_x -= 1 # the last segments must be horizontal
        else:
            assert(self.y == 0)
            delta_y -= 1 # the last segments must be horizontal

        assert(delta_y >= 0 and delta_x >= 0)
        self.subladderLength = delta_x + delta_y
        candidiateGoUpSteps = range(self.subladderLength)
        self.it = iter(itertools.combinations(candidiateGoUpSteps, delta_y))
    def __iter__(self):
        return self
    def __next__(self):
        goUpSteps = next(self.it)
        r = [(self.x, self.y)]
        for x in range(self.subladderLength):
            if x in goUpSteps:
                r.append((r[-1][0], r[-1][1] + 1))
            else:
                r.append((r[-1][0] + 1, r[-1][1]))
        if self.isUpperLadder:
            assert(r[-1][0] + 1 == self.dx and r[-1][1] == self.dy)
        else:
            assert(r[-1][0] == self.dx and r[-1][1] + 1 == self.dy)
        r.append((self.dx, self.dy))
        return r

#### test class stragety: see crowdscreen paper figure 1(c)
# s = strategy(5, 0.5, 0.2, 0.1)
# s.grid[0][0] = CONN
# s.grid[0][1] = CONN
# s.grid[0][2] = PASS
# s.grid[1][0] = CONN
# s.grid[1][1] = FAIL
# s.grid[2][0] = FAIL
# 
# s.calc()
# print(s.eEach)
# print(s.e)
# print(s.c)

#### test ladderGenerator
lg = ladderGenerator(3, ladderGenerator.UPPER_LADDER)
lg.reset((0, 0), (3, 3))
for x in lg:
    print(x)
print('--------------------')
lg = ladderGenerator(3, ladderGenerator.LOWER_LADDER)
lg.reset((0, 0), (3, 3))
for x in lg:
    print(x)

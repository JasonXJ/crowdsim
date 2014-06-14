PASS = BLUE = 1
FAIL = RED = 2
CONN = GREEN = 0
UNREACHABLE = -1

class ViolateM(Exception):
    pass
class NotTerminating(Exception):
    pass
class MeetUnreachableNode(Exception):
    pass
        

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
    def __init__(self, m, s, e0, e1, gridInitValue = CONN):
        self.m = m
        self.s = s
        self.e0 = e0
        self.e1 = e1
        self.grid = self._getGrid(gridInitValue)
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
        """check the grid and ensure unreachable nodes are labeled correctly.
        
        If the strategy is not terminating, this function will raise `NotTerminating` instead of `ViolateM`"""
        visitedGrid = self._getGrid(False)
        self._checkGrid_visit(0, 0, visitedGrid)
        for x in range(self.m + 1):
            for y in range(self.m + 1):
                if visitedGrid[x][y] == False:
                    self.grid[x][y] = UNREACHABLE
                elif x + y > self.m:
                    raise ViolateM

    def _checkGrid_visit(self, x, y, visitedGrid):
        if x > self.m or y > self.m:
            raise NotTerminating
        if visitedGrid[x][y] == True:
            return
        visitedGrid[x][y] = True
        gridValue = self.grid[x][y]
        if gridValue == UNREACHABLE:
            raise MeetUnreachableNode
        if gridValue == CONN: # continue
            self._checkGrid_visit(x + 1, y, visitedGrid)
            self._checkGrid_visit(x, y + 1, visitedGrid)


    def _getGrid(self, initValue = 0):
        return [ [initValue for i in range(self.m + 1)] for x in range(self.m + 1) ]
    def _calcP(self): # should call checkGrid() before call this function
        if not self.p0 or not self.p1:
            self.p0 = self._getGrid(0)
            self.p1 = self._getGrid(0)
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
    def __str__(self):
        return 'e: {:.3f}, c: {:.3f}'.format(self.e, self.c)

import itertools
class ladderGenerator:
    """This class iterates though all ladder start from y/x axis and ensures the last segment of the ladder is horizontal/vertical.
    
    The return list includes points of the whole ladder except the start point
    and the end point (decision point)."""
    UPPER_LADDER = 0
    LOWER_LADDER = 1
    def __init__(self, ladderType):
        self.isUpperLadder = False
        if ladderType == self.UPPER_LADDER:
            self.isUpperLadder = True

    def reset(self, startPoint, decisionPoint, restrictPoints = None):
        """if restrictPoints is not None, then the ladder will not contain points in it."""

        if restrictPoints:
            self.restrictPoints = set(restrictPoints)
            assert(startPoint not in self.restrictPoints and decisionPoint not in self.restrictPoints)
        else:
            self.restrictPoints = set()

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
            delta_y -= 1 # the last segments must be vertical

        assert(delta_y >= 0 and delta_x >= 0)
        self.subladderLength = delta_x + delta_y
        self.it = None
        if self.subladderLength > 0:
            candidiateGoUpSteps = range(self.subladderLength)
            self.it = iter(itertools.combinations(candidiateGoUpSteps, delta_y))
        else:
            # special case, delta_x == delta_y == 0. if it is upper ladder, dx
            # = x + 1 and dy = y. if it is lower ladder, dx = x and dy = y + 1
            self.hasGotSpecial = False

    def __iter__(self):
        return self

    def __next__(self):
        if self.subladderLength == 0:
            if self.hasGotSpecial:
                raise StopIteration
            self.hasGotSpecial = True
            return []
        while True:
            goUpSteps = next(self.it)
            for x in range(0, self.subladderLength):
                if x in goUpSteps:
                    if x != 0:
                        r.append((r[-1][0], r[-1][1] + 1))
                    else:
                        r = [(self.x, self.y + 1)]
                else:
                    if x != 0:
                        r.append((r[-1][0] + 1, r[-1][1]))
                    else:
                        r = [(self.x + 1, self.y)]
                if r[-1] in self.restrictPoints:
                    break
            else:
                if self.isUpperLadder:
                    assert(r[-1][0] + 1 == self.dx and r[-1][1] == self.dy)
                else:
                    assert(r[-1][0] == self.dx and r[-1][1] + 1 == self.dy)
                return r

def getBestLadderStrategy(t, m, s, e0, e1):
    # special strategy case: terminates at (0,0)
    tempStrategy = strategy(m, s, e0, e1)
    if s < 0.5:
        tempStrategy.grid[0][0] = FAIL
    else:
        tempStrategy.grid[0][0] = PASS
    tempStrategy.calc()
    if tempStrategy.e <= t:
        # if this happen, tempStrategy mush be the best (lowest cost) stratyge
        return tempStrategy
    bestStrategy = None
    # normal case: x > 0 and y > 0
    # in additional, decX >= x and decY >= y, where (decX, decY) is the decision point
    upper = ladderGenerator(ladderGenerator.UPPER_LADDER)
    lower = ladderGenerator(ladderGenerator.LOWER_LADDER)
    for x in range(1, m+1):
        for y in range(1, m-x+2): # x + y <= m + 1
            for decX in range(x, m+1):
                for decY in range(y, m - decX + 2): # decX + decY <= m + 1
                    upper.reset((0, y), (decX, decY))
                    for upperLadder in upper:
                        # restrict lower ladder so that it won't overlap upper ladder
                        lower.reset((x, 0), (decX, decY), upperLadder)
                        for lowerLadder in lower:
                            tempStrategy = strategy(m, s, e0, e1)
                            for points in lowerLadder:
                                tempStrategy.grid[points[0]][points[1]] = FAIL
                            tempStrategy.grid[x][0] = FAIL
                            for points in upperLadder:
                                tempStrategy.grid[points[0]][points[1]] = PASS
                            tempStrategy.grid[0][y] = PASS
                            tempStrategy.grid[decX][decY] = PASS
                            try:
                                # the stragety may violate the restriction of `m`
                                tempStrategy.calc()
                            except ViolateM:
                                pass
                            else:
                                if tempStrategy.e <= t:
                                    if (bestStrategy is None) or (tempStrategy.c < bestStrategy.c):
                                        bestStrategy = tempStrategy
    return bestStrategy

def calcLadderShapeCount(m):
    from math import factorial
    def nCr(n, r):
        return factorial(n) / factorial(r) / factorial(n-r)
    count = 0
    for x in range(1, m+1):
        for y in range(1, m-x+2):
            for decX in range(x, m+1):
                for decY in range(y, m - decX + 2):
                    count += nCr(decX+decY-y, decX) * nCr(decX+decY-x, decY)
    return count

#### test class stragety: see crowdscreen paper figure 1(c)
#s = strategy(5, 0.5, 0.2, 0.1)
#s.grid[0][2] = PASS
#s.grid[1][1] = FAIL
#s.grid[2][0] = FAIL
#
#s.calc()
#print(s.eEach)
#print(s.e)
#print(s.c)

#### test ladderGenerator
#lg = ladderGenerator(ladderGenerator.UPPER_LADDER)
#lg.reset((0, 1), (3, 3))
#for x in lg:
#    print(x)
#print('--------------------')
#lg2 = ladderGenerator(ladderGenerator.LOWER_LADDER)
#lg2.reset((1, 0), (3, 3), [(2,2), (3, 0)])
#for x in lg2:
#    print(x)
#print('--------------------')
#lg2.reset((1, 0), (3, 3))
#for x in lg2:
#    print(x)
#print('--------------------')
#lg2.reset((2, 0), (3, 2))
#for x in lg2:
#    print(x)
#print('--------------------')
#lg2.reset((2, 0), (2, 1)) # special case
#for x in lg2:
#    print(x)

#### getBestLadderStrategy test
#print(getBestLadderStrategy(0.2, 0, 0.8, 0.2, 0.2))
#print(getBestLadderStrategy(0.2, 4, 0.8, 0.2, 0.2))
## the follow case is the example of figure 1(c)
#print(getBestLadderStrategy(0.2, 3, 0.5, 0.2, 0.1))
## 
#print(getBestLadderStrategy(0.2, 10, 0.5, 0.2, 0.1))

#for m in range(3, 14):
#    print('m: {}\t shape count: {}'.format(m, calcLadderShapeCount(m)))

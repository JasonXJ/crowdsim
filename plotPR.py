import matplotlib.pyplot as plt
import random
from itertools import chain

def plotPRCurve(answers):
    TRUE_POSITIVE = 1
    FALSE_POSITIVE = 2
    predictTrueList = []
    predictFalseList = []
    actureTrueCount = 0
    for a in answers:
        if a.label == 1:
            if a.task.trueLabel == 1:
                predictTrueList.append(TRUE_POSITIVE)
                actureTrueCount += 1
            else:
                predictTrueList.append(FALSE_POSITIVE)
        else: # 把这部分也当成predict true的
            if a.task.trueLabel == 1:
                predictFalseList.append(TRUE_POSITIVE)
                actureTrueCount += 1
            else:
                predictFalseList.append(FALSE_POSITIVE)

    random.shuffle(predictTrueList)
    random.shuffle(predictFalseList)
    recallPoints = [0]
    precisionPoints = [1]
    truePositiveCount = 0
    for i, x in enumerate(chain(predictTrueList, predictFalseList), start = 1):
        if x == TRUE_POSITIVE:
            truePositiveCount += 1
        recallPoints.append(truePositiveCount / actureTrueCount)
        precisionPoints.append(truePositiveCount / i)
    plt.plot(recallPoints, precisionPoints)
    plt.axis([0,1,0,1.1])
    plt.show()

#from crowdsim.common import SimpleTask, SimpleAnswer
#
#taskPositive = SimpleTask(1, 2, 1)
#taskNegetive = SimpleTask(2, 2, 0)
#answers = [SimpleAnswer(taskPositive, 1),
#        SimpleAnswer(taskNegetive, 1),
#        SimpleAnswer(taskNegetive, 0),
#        SimpleAnswer(taskPositive, 0),
#        SimpleAnswer(taskPositive, 1)]
#
#plotPRCurve(answers)

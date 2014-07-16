#!/usr/bin/env python3

import logging
logging.basicConfig(level = logging.DEBUG, filename = 'amttest.log',
        filemode='w', format='%(levelname)s %(asctime)s %(module)s: %(message)s')

import crowdsim, sys
from crowdsim.agent.AMT import HITParameters, AMT as AMTAgent, flags
from crowdsim.workerpool_amt import amt as wp_amt
import configparser, builtins, re
from collections import namedtuple

AnswerWithTime = namedtuple('AnswerWithTime', 'workerId, task, label, text, createTime, acceptTime, submitTime')

class csvReader:
    def __init__(self, fileobject, batchSize):
        self.batchTitles = self.titles = [ x.strip() for x in fileobject.readline().strip().split(',')]
        self.batchDatas = self.datas = []
        for l in fileobject:
            self.datas.append([x.strip() for x in l.strip().split(',')])

        if batchSize > 1:
            self.batchTitles = self.titles[:]
            match = re.match('(.+?)(\d+)$', self.titles[-1])
            namebase, digit = match.group(1), int(match.group(2))
            width = len(self.titles)
            for batch in range(batchSize-1):
                for x in range(width):
                    digit += 1
                    self.batchTitles.append(namebase + str(digit))
            self.batchDatas = []
            def deepExpand(ll):
                r = []
                for x in ll:
                    r.extend(x)
                return r
            for cursorB in range(0, len(self.datas), batchSize):
                self.batchDatas.append(deepExpand(self.datas[cursorB:cursorB+batchSize]))
            assert(batchSize < len(self.datas))
            if len(self.batchDatas[-1]) != len(self.batchDatas[0]):
                difference = len(self.batchDatas[0]) - len(self.batchDatas[-1])
                self.batchDatas[-1].extend(self.batchDatas[0][:difference])

class preDeducer(crowdsim.deducer.BaseDeducer):
    re_questionId = re.compile('question(\d+)$')
    def __init__(self, batchSize, realGenerator, collect = False):
        self.batchSize = batchSize
        self.collect = collect
        self.realGenerator = realGenerator

    def flattenAnswerList(self, answerList):
        result = [ None for x in range(self.batchSize)]
        for answer in answerList:
            id = int(self.re_questionId.match(answer['QuestionIdentifier']).group(1))
            if self.collect:
                result[id-1] = answer['FreeText']
            else:
                assert(answer['FreeText'] == 'yes' or answer['FreeText'] == 'no')
                result[id-1] = 1 if answer['FreeText'] == 'yes' else 0
        return result

    def link(self, workerPool):
        self.workerPool = workerPool
        self.assigner = self.workerPool.assigner
        if self.batchSize > 1:
            self.answerList = [] # unpacked answer list
            for batchAnswer in self.workerPool:
                batchId = batchAnswer.task.id
                startId = batchId * self.batchSize
                hitInfo, assignment = batchAnswer.label
                for a in self.flattenAnswerList(assignment[1]):
                    if startId >= self.realGenerator.taskCount:
                        startId %= self.realGenerator.taskCount
                    self.answerList.append(batchAnswer._replace(task = self.realGenerator.id_to_task[startId], label = a))
                    startId += 1
        else:
            self.answerList = self.workerPool.answerList

    def __iter__(self):
        return iter(self.answerList)

def generateHPConstructor(csv, lifetimeInSeconds, layoutId, title, description,
        rewardAmount, assignmentDurationInSeconds, keywords,
        autoApprovalDelayInSeconds, **kwargs):
    param = HITParameters(lifetimeInSeconds, useTypeId = False, **kwargs)
    param.setTypeProperties(title, description, rewardAmount,
            assignmentDurationInSeconds, keywords, autoApprovalDelayInSeconds)
    param.setLayout(layoutId)
    def inner(assignment):
        param.setLayoutParameter(
                {title : attr for title, attr in zip(csv.batchTitles, csv.batchDatas[assignment.task.id])})
        param.parameters['MaxAssignments'] = assignment.duplicate
        param.parameters['RequesterAnnotation'] = 'task id = {}'.format(assignment.task.id)
        return param
    return inner

def answerConstructor(hitInfo, assignment):
    worker = assignment[2].findtext('WorkerId')
    ct = hitInfo['HITElement'].findtext('CreationTime')
    at = assignment[2].findtext('AcceptTime')
    st = assignment[2].findtext('SubmitTime')
    if batchSize > 1:
        label = (hitInfo, assignment)
    else:
        label = 1 if assignment[1][0]['FreeText'] == 'yes' else 0
    return AnswerWithTime(worker, hitInfo['task'], label, ct, at, st)

def constructComponent(componentName):
    obj = eval(config['crowdsim'][componentName])
    if type(obj) == builtins.type:
        obj = obj()
    return obj

config = configparser.ConfigParser()
config.read(sys.argv[1])

outputMetric = False
if 'workerpool' in config['crowdsim']:
    # do not use the crowd, use simulation, ignore AMT setting
    outputMetric = True
    with open(config['others']['input_answers']) as f:
        trueLabelGenerator = [int(l) for l in f]
    g = crowdsim.generator.GeneralGenerator(len(trueLabelGenerator), 2, trueLabelGenerator)
    a = constructComponent('assigner')
    dw = w = constructComponent('workerpool')
    d = constructComponent('deducer')
    crowdsim.linkAll(g, a, w, d)
else:
    # initialization
    collect = config['others'].get('collect', False) == 'True'
    batchSize = int(config['others'].get('batchSize', 1))
    csv = csvReader(open(config['others']['input_questions']), batchSize)

    amtagent = AMTAgent(config['AMT']['KeyId'], config['AMT']['SecretKey'], debug = True)
    hpConstructor = generateHPConstructor(csv, config['AMT_HIT']['Lifetime'],
            config['AMT_HIT']['LayoutId'],
            config['AMT_HIT']['Title'],
            config['AMT_HIT']['Description'],
            config['AMT_HIT']['Reward'],
            config['AMT_HIT']['AssignmentDurationInSeconds'],
            config['AMT_HIT']['Keywords'],
            config['AMT_HIT']['AutoApprovalDelayInSeconds'],
            )


    # construct crowdsim system
    labelCountGenerator = lambda x : None
    trueLabelGenerator = lambda x : None
    if not collect:
        labelCountGenerator = 2
        if 'input_answers' in config['others']:
            with open(config['others']['input_answers']) as f:
                trueLabelGenerator = [int(l) for l in f]
                outputMetric = True
        

    a = constructComponent('assigner')
    w = wp_amt(amtagent, hpConstructor, answerConstructor, responseGroup_createHIT = [flags.responseGroup.minimal, flags.responseGroup.hitDetail])
    w.sleepTime = 30

    if collect == True:
        d = crowdsim.deducer.Passer()
    else:
        d = constructComponent('deducer')

    if batchSize == 1:
        g = crowdsim.generator.GeneralGenerator(len(csv.datas), labelCountGenerator, trueLabelGenerator)
        dw = preDeducer(batchSize, g, collect)
        crowdsim.linkAll(g,a,w,dw)
    else:
        g_batch = crowdsim.generator.GeneralGenerator(len(csv.batchDatas), lambda x : None, lambda x : None)
        g = crowdsim.generator.GeneralGenerator(len(csv.datas), labelCountGenerator, trueLabelGenerator)
        dw = preDeducer(batchSize, g, collect)
        crowdsim.linkAll(g_batch,a,w,dw)
    d.link(dw)



if outputMetric:
    cm = crowdsim.getConfusionMatrix(d, True)
    metrics = crowdsim.getBinaryTaskMetrics(cm)
    print(metrics)

with open(config['others']['Output_answers'], 'w') as answerFile:
    for x in dw.answerList:
        print(str(x), file = answerFile)

with open(config['others']['Output_deduced_answers'], 'w') as answerFile:
    if outputMetric:
        print(metrics, file = answerFile)
    for x in d.answerList:
        print(str(x), file = answerFile)

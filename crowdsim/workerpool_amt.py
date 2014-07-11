from .common import *
from .workerpool import BaseWorkerPool
import logging
from .agent.AMT import flags, TimeUnit as tu
import time

# FIXME: fix all docstring

class amt(BaseWorkerPool):
    def __init__(self, amtAgent, HITParameterConstructor, answerConstructor):
        self.agent = amtAgent
        self.HPConstructor = HITParameterConstructor
        self.answerConstructor = answerConstructor
        self.extendTime = 1 * tu.day
        self.sleepTime = 5 * tu.minute

    def _agentWrapper(self, methodName, *args, **kwargs):
        r = getattr(self.agent, methodName)(*args, **kwargs)
        assert(r != False and r != None)
        return r

    def __iter__(self):
        return iter(self.answerList)
        
    def link(self, assigner):
        self.assigner = assigner
        self.answerList = []
        self.task2hitInfo = {}
        self.hitId2info = {}
        self.assignmentIds = set()
        while True:
            try:
                aa = self.assigner.assign2()
            except RunOutOfAllTask:
                # get all answers before leaving
                totalDuplicate = 0
                for hitInfo in self.task2hitInfo.values():
                    totalDuplicate += hitInfo['duplicate']
                logging.info('Encounter RunOutOfAllTask: '\
                        'going to leave after geting all {} answers'.format(totalDuplicate))
                while totalDuplicate != len(self.answerList):
                    self.updateAnswers()
                logging.info('Finished')
                break
            except RunOutOfActiveTask:
                logging.info('Encounter RunOutOfActiveTask')
                self.updateAnswers()
            else:
                if aa.task in self.task2hitInfo:
                    # extend hit
                    logging.info('Extending HIT: task.id = {} duplicate = {}'.format(aa.task.id, aa.duplicate))
                    hitInfo = self.task2hitInfo[aa.task]
                    self._agentWrapper('extendHIT', hitInfo['id'], aa.duplicate, self.extendTime)
                    hitInfo['duplicate'] += aa.duplicate
                else:
                    # create new hit
                    logging.info('Creating HIT: task.id = {} assignments = {}'.format(aa.task.id, aa.duplicate))
                    hitInfo = {}
                    hp = self.HPConstructor(aa)
                    hitInfo['id'] = self._agentWrapper('createHIT', hp)[0]
                    hitInfo['task'] = aa.task
                    hitInfo['duplicate'] = aa.duplicate
                    hitInfo['answerCount'] = 0

                    self.task2hitInfo[aa.task] = hitInfo
                    self.hitId2info[hitInfo['id']] = hitInfo

    def updateAnswers(self):
        updated = False
        while True:
            logging.info('Updating answers ...')
            hitIds = self._agentWrapper('getReviewableHITs', sortProperty = flags.sortProperty.enumeration)
            for id in hitIds:
                if id not in self.hitId2info:
                    continue
                # XXX: set the hit to reviewing
                hitInfo = self.hitId2info[id]
                if hitInfo['answerCount'] != hitInfo['duplicate']:
                    assignments = self._agentWrapper('getAssignmentsForHIT', id)
                    for ass in assignments:
                        if ass[0] not in self.assignmentIds:
                            self.assignmentIds.add(ass[0])
                            updated = True
                            answer = self.answerConstructor(hitInfo['task'], ass)
                            self.answerList.append(answer)
                            hitInfo['answerCount'] += 1

                            self.assigner.update(answer.workerId, answer.task, answer.label)

                    assert(hitInfo['answerCount'] == len(assignments))
                    if hitInfo['answerCount'] != hitInfo['duplicate']:
                        # Still unequal means hit became reviewable because of expiration. let extend it.
                        logging.info('Task {} expired, extending it'.format(hitInfo['task'].id))
                        self._agentWrapper('extendHIT', hitInfo['id'], expirationIncrementInSeconds =
                                self.extendTime)
            if updated:
                logging.info('Finish updating (total answer count = {})'.format(len(self.answerList)))
                break
            logging.info('Fail to update (total answer count = {}): sleep for {} seconds'.format(self.sleepTime))
            time.sleep(self.sleepTime)

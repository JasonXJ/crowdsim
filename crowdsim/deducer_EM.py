#Authors:  Jiannan Wang
#DateTime: 2011-11-03 13:43
#Function: Implement the get-another-label algorithm
from . import common
from .deducer import BaseDeducer

class EM(BaseDeducer):
    def __init__(self, iterTimes):
        self.iterTimes = iterTimes

    def link(self, workerPool):
        self.workerPool = workerPool
        self.worker_example_label_set = []
        self.example_to_worker_label = {}
        self.worker_to_example_label = {}
        self.label_set = [0, 1]
        self.id2Task = {}
        for a in workerPool:
            self.worker_example_label_set.append((a.workerId, a.task.id, a.label))
            self.example_to_worker_label.setdefault(a.task.id, []).append((a.workerId, a.label))
            self.worker_to_example_label.setdefault(a.workerId, []).append((a.task.id, a.label))
            self.id2Task[a.task.id] = a.task
        self.EstimateMaximize()

    def __iter__(self):
        return iter(self.answerList)
    
    def MajorityVote(self, worker_example_label_set):
        example_to_decision_label = {}
        example_to_label_weight = {}
        for worker,example,label in worker_example_label_set:
            if example not in example_to_label_weight:
                example_to_label_weight[example] = {}
            example_to_label_weight[example][label] = example_to_label_weight[example].get(label,0)+1
        for example,label_weight in example_to_label_weight.items():
            max_label = None
            max_weight = 0
            for label, weight in label_weight.items():
                if weight > max_weight:
                    max_weight = weight
                    max_label = label
            example_to_decision_label[example] = max_label
        return example_to_decision_label
            
    def ConfusionMatrix(self, worker_to_example_label, example_to_softlabel):
        worker_to_confusion_matrix = {}
        worker_to_finallabel_weight = {}
        worker_to_finallabel_workerlabel_weight = {}

        for worker, example_label in worker_to_example_label.items():
            if worker not in worker_to_finallabel_weight:
                worker_to_finallabel_weight[worker] = {}
            if worker not in worker_to_finallabel_workerlabel_weight:
                worker_to_finallabel_workerlabel_weight[worker] = {}
            for example, workerlabel in example_label:
                softlabel =  example_to_softlabel[example]
                for finallabel, weight in softlabel.items():
                    worker_to_finallabel_weight[worker][finallabel] = worker_to_finallabel_weight[worker].get(finallabel, 0)+weight
                    if finallabel not in worker_to_finallabel_workerlabel_weight[worker]:
                        worker_to_finallabel_workerlabel_weight[worker][finallabel] = {}
                    worker_to_finallabel_workerlabel_weight[worker][finallabel][workerlabel] = worker_to_finallabel_workerlabel_weight[worker][finallabel].get(workerlabel, 0)+weight
                    
    
        worker_to_confusion_matrix = worker_to_finallabel_workerlabel_weight
        for worker, finallabel_workerlabel_weight in worker_to_finallabel_workerlabel_weight.items():
            for finallabel, workerlabel_weight in finallabel_workerlabel_weight.items():
                for workerlabel, weight in workerlabel_weight.items():
                    if worker_to_finallabel_weight[worker][finallabel] == 0:
                        assert weight == 0
                    else:
                        worker_to_confusion_matrix[worker][finallabel][workerlabel] = weight*1.0/worker_to_finallabel_weight[worker][finallabel]
        return worker_to_confusion_matrix
                    
    def PriorityProbability(self, example_to_softlabel):
        label_to_priority_probability = {}
        for example, softlabel in example_to_softlabel.items():
            for label, probability in softlabel.items():
                label_to_priority_probability[label] = label_to_priority_probability.get(label,0)+probability
        for label, count in label_to_priority_probability.items():
            label_to_priority_probability[label] = count*1.0/len(example_to_softlabel)
        return label_to_priority_probability
  
    
    def ProbabilityMajorityVote(self, example_to_worker_label, label_to_priority_probability, worker_to_confusion_matrix):
        example_to_sortlabel = {}
        for example, worker_label_set in example_to_worker_label.items():
            sortlabel = {}
            total_weight = 0
            for final_label, priority_probability in label_to_priority_probability.items():
                weight = priority_probability
                #print example, weight,
                for (worker, worker_label) in worker_label_set:
                    try:
                        weight *= worker_to_confusion_matrix[worker][final_label][worker_label]
                        #print worker_to_confusion_matrix[worker][final_label][worker_label],
                    except:
                        weight = 0
                        #print 0 
                #print
                total_weight += weight
                sortlabel[final_label] = weight
            for final_label, weight in sortlabel.items():
                if total_weight == 0:
                    assert weight == 0
                else:
                    sortlabel[final_label] = weight*1.0/total_weight
            example_to_sortlabel[example] = sortlabel
        #print example_to_sortlabel
        return example_to_sortlabel
                     
    def InitSoftLabel(self, worker_example_label_set):
        example_to_softlabel = {}
        for worker,example,label in worker_example_label_set:
            if example not in example_to_softlabel:
                example_to_softlabel[example] = {}
            example_to_softlabel[example][label] = example_to_softlabel[example].get(label,0)+1
        for example,softlabel in example_to_softlabel.items():
            label_num = 0
            for label, count in softlabel.items():
                label_num += count
            for label, count in softlabel.items():
                softlabel[label] = count*1.0/label_num
        #print example_to_softlabel
        return example_to_softlabel

    def EstimateMaximize(self):
        worker_to_confusion_matrix = {}  
        example_to_probability_label = {}
        label_to_priority_probability = {}
        worker_example_label_set = self.worker_example_label_set
        example_to_worker_label = self.example_to_worker_label
        worker_to_example_label = self.worker_to_example_label
        label_set = self.label_set
        #Inital-Step
        example_to_softlabel = self.InitSoftLabel(worker_example_label_set)
        for i in range(self.iterTimes):
            label_to_priority_probability = self.PriorityProbability(example_to_softlabel)
            worker_to_confusion_matrix = self.ConfusionMatrix(worker_to_example_label, example_to_softlabel)
            example_to_softlabel = self.ProbabilityMajorityVote(example_to_worker_label, label_to_priority_probability, worker_to_confusion_matrix) 
        #self.OutputDecisionLabel("./data/post-majority-vote.txt", example_to_softlabel)
        self.answerList = []
        for taskId, softlabel in example_to_softlabel.items():
            self.answerList.append(common.SimpleAnswer(self.id2Task[taskId], max(softlabel, key=softlabel.get)))

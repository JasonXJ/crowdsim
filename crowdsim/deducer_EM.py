#! /usr/bin/env python
#coding=utf-8
#Authors:  Jiannan Wang
#DateTime: 2011-11-03 13:43
#Function: Implement the get-another-label algorithm
import sys
import math

class GetAnotherLabel:
    def __init__(self, filename):
        self.worker_example_label_set = []
        self.example_to_worker_label = {}
        self.worker_to_example_label = {}
        self.label_set = []
        self.label_count = {}
        f = open(filename)
        for line in f.xreadlines():
            line = line.strip()
            if not line:
                continue
            items =  line.split()
            #print items
            self.worker_example_label_set.append(items)
            self.example_to_worker_label.setdefault(items[1], []).append((items[0], items[2]))
            self.worker_to_example_label.setdefault(items[0], []).append((items[1], items[2]))
            self.label_count[items[2]] = self.label_count.get(items[2], 0)+1
        self.label_set = self.label_count.keys()
    
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
        # Not Compitable to multi-labels
        #label_set = ['0', '1']
        #for worker, confusion_matrix in worker_to_confusion_matrix.items():
        #    for label in label_set:
        #        if not confusion_matrix.has_key(label):
        #            confusion_matrix[label] = {label:1} 
        #        print confusion_matrix
        #        if not confusion_matrix[label].has_key('0'):
        #            confusion_matrix[label]['0'] = 1-confusion_matrix[label]['1']
        #        elif not confusion_matrix[label].has_key('1'):
        #            confusion_matrix[label]['1'] = 1-confusion_matrix[label]['0']
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
                     
    def OutputDecisionLabel(self, filename, example_to_softlabel):
        f = open(filename, "w")
        import operator
        sorted_example_to_softlabel = sorted(example_to_softlabel.items(), key=operator.itemgetter(0))
        for example, softlabel in sorted_example_to_softlabel:
            decision_label = max(softlabel, key=softlabel.get)
            f.write("%s\t%s\n" %(example, decision_label))
    #        print example, decision_label
        #print
        f.close()
    def OutputSoftLabel(self, filename, example_to_softlabel):
        f = open(filename, "w")
        import operator
        sorted_example_to_softlabel = sorted(example_to_softlabel.items(), key=lambda x:-x[1]['1'])
        for example, softlabel in sorted_example_to_softlabel:
            decision_label = max(softlabel, key=softlabel.get)
            f.write("%s\t%s\n" %(example, softlabel['1']))
            softlabel_items = sorted(softlabel.items(), key=lambda x: x[0])
            sum = 0
            for label, value in softlabel_items:
                sum += value
            assert math.fabs(sum-1) <= 1e-6;
    #        print example, decision_label
        #print
        f.close()
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

    def SetArray(self, array, label_0, label_1, value):
        if not array.has_key(label_0):
            array[label_0] = {}
        array[label_0][label_1] = value

    def GetArray(self, array, label_0, label_1):
        if not array.has_key(label_0):
            return 0
        return array[label_0].get(label_1, 0)

    def EstimateMaximize(self, iter = 10):
        worker_to_confusion_matrix = {}  
        example_to_probability_label = {}
        label_to_priority_probability = {}
        worker_example_label_set = self.worker_example_label_set
        example_to_worker_label = self.example_to_worker_label
        worker_to_example_label = self.worker_to_example_label
        label_set = self.label_set
        #Inital-Step
        example_to_softlabel = self.InitSoftLabel(worker_example_label_set)
        self.OutputDecisionLabel("./data/pre-majority-vote.txt", example_to_softlabel)
        while iter>0:
            label_to_priority_probability = self.PriorityProbability(example_to_softlabel)
            print label_to_priority_probability
            worker_to_confusion_matrix = self.ConfusionMatrix(worker_to_example_label, example_to_softlabel)
            for worker, confusion_matrix in worker_to_confusion_matrix.items():
                print  worker, confusion_matrix
            example_to_softlabel = self.ProbabilityMajorityVote(example_to_worker_label, label_to_priority_probability, worker_to_confusion_matrix) 
    #        for example, softlabel in example_to_softlabel.items():
     #           print example, softlabel
            iter -= 1
        self.OutputDecisionLabel("./data/post-majority-vote.txt", example_to_softlabel)
        self.OutputSoftLabel("./data/softlabel.txt", example_to_softlabel)
        cost_matrix = {}
        for label_0 in label_set:
            for label_1 in label_set:
                self.SetArray(cost_matrix, label_0, label_1, 0 if label_0 == label_1 else 1)
                cost_matrix[label_0][label_1] = 0 if label_0 == label_1 else 1
        print >>sys.stderr, cost_matrix
        worker_to_quality = self.WorkerQuality(worker_to_confusion_matrix, label_to_priority_probability, cost_matrix)
        self.OutputWorkerQuality("./data/worker-quality.txt", worker_to_quality)
        #self.DebugSoftLabel(example_to_softlabel)

    def InitPriorityProbability(self, label_set):
        label_to_priority_probability = {}
        for label in label_set:
            label_to_priority_probability[label] = 1.0/len(label_set)
        return label_to_priority_probability

    def InitConfusionMatrix(self, workers, label_set):
        worker_to_confusion_matrix = {}
        for worker in workers:
            if worker not in worker_to_confusion_matrix:
                worker_to_confusion_matrix[worker] = {}
            for label1 in label_set:
                if label1 not in worker_to_confusion_matrix[worker]:
                    worker_to_confusion_matrix[worker][label1] = {}
                for label2 in label_set:
                    if label1 == label2:
                        worker_to_confusion_matrix[worker][label1][label2] = 0.9
                    else:
                        worker_to_confusion_matrix[worker][label1][label2] = 0.1/(len(label_set)-1)
        return worker_to_confusion_matrix
    
    def MyDivide(self, a, b):
        if b == 0:
            return 0
        return a*1.0/b
    def WorkerQuality(self, worker_to_confusion_matrix, label_to_priority_probability, cost_matrix):
        worker_to_quality = {}
        label_set = label_to_priority_probability.keys()
        print label_to_priority_probability
        for worker, confusion_matrix in worker_to_confusion_matrix.items():
            reverse_confusion_matrix = {}
            for label_0 in label_set:
                for label_1 in label_set:
                    self.SetArray(reverse_confusion_matrix, label_1, label_0, self.GetArray(confusion_matrix, label_0, label_1)*label_to_priority_probability[label_0])
            label_pr = {}
            for label_0 in label_set:
                pr = 0
                for label_1 in label_set:
                    pr += reverse_confusion_matrix[label_0][label_1]
                label_pr[label_0] = pr

            for label_0 in label_set:
                for label_1 in label_set:
                    reverse_confusion_matrix[label_0][label_1] = self.MyDivide(reverse_confusion_matrix[label_0][label_1], label_pr[label_0])

            total_cost = 0
            print worker
            print confusion_matrix
            print reverse_confusion_matrix
            print
            for label_0 in label_set:
                cost = 0
                spammer_cost = 0
                for label_1 in label_set:
                    for label_2 in label_set:
                        cost += reverse_confusion_matrix[label_0][label_1]*reverse_confusion_matrix[label_0][label_2]*cost_matrix[label_1][label_2]
                        spammer_cost += label_to_priority_probability[label_1]*label_to_priority_probability[label_2]*cost_matrix[label_1][label_2]
                total_cost += cost*label_pr[label_0]
            #precision = reverse_confusion_matrix['1']['1']
            #recall = confusion_matrix['1']['1']
            #fmeasure = self.MyDivide(2*precision*recall, precision+recall)
            #worker_to_quality[worker] = (precision, recall, fmeasure, 1-total_cost/spammer_cost)
            worker_to_quality[worker] = (None, None, None, 1-total_cost/spammer_cost)
        return worker_to_quality

    def OutputWorkerQuality(self, filename, worker_to_quality):
        f = open(filename, "w")
        for worker, quality in worker_to_quality.items():
            f.write("%s\t" %(worker))
            f.write("{}\t{}\t{}\t{}\n".format(*quality))
        f.close()
        
if __name__ == "__main__":
    filename = sys.argv[1]
    iter = int(sys.argv[2])
    instance = GetAnotherLabel(filename)
    instance.EstimateMaximize(iter)

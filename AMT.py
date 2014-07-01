#!/usr/bin/env python3

import time, hmac, hashlib, base64
import requests
import xml.etree.ElementTree as et
from collections import namedtuple

sPrice = namedtuple('sPrice', 'Amount, CurrencyCode')
sHITLayoutParameter = namedtuple('sHITLayoutParameter', 'Name, Value')

class AMT:
    def __init__(self, keyId, secret, useSandbox = True, verify = True):
        self.keyId = keyId
        self.bSecret = secret.encode('utf-8')
        self.verify = verify
        if useSandbox:
            self.service_url='https://mechanicalturk.sandbox.amazonaws.com/'
        else:
            self.service_url='https://mechanicalturk.amazonaws.com/'

    def _generateSignature(self, parameters):
        msg = parameters['Service'] + parameters['Operation'] + parameters['Timestamp']
        s = hmac.new(self.bSecret, msg.encode('utf-8'), hashlib.sha1).digest()
        return base64.encodestring(s).strip()

    def _isNamedtuple(self, value):
        try:
            value._fields
        except AttributeError:
            return False
        return True

    def _flattenParameters(self, parameters):
        newParameters = parameters.copy()
        for key, value in parameters.items():
            try:
                iter(value)
            except TypeError:
                # normal value, do not need to modify
                pass
            else:
                # iterable, check if is bytes or str
                if not (isinstance(value, str) or isinstance(value, bytes)):
                    self._flattenParameters_iterable(newParameters, key)
        return newParameters

    def _flattenParameters_iterable(self, parameters, key):
        value = parameters[key]
        if self._isNamedtuple(value):
            self._flattenParameters_namedtuple(parameters, value, key + '.1.')
        else:
            for i, x in enumerate(value, 1):
                if self._isNamedtuple(x):
                    # iterable contains namedtuple
                    self._flattenParameters_namedtuple(parameters, x, '{}.{}.'.format(key, i))
                else:
                    # iterable contains normal value
                    parameters['{}.{}'.format(key, i)] = x
        del parameters[key]

    def _flattenParameters_namedtuple(self, parameters, value, prefix = ''):
        for name in value._fields:
            parameters[prefix + name] = getattr(value, name)

    def request(self, operation, parameters = None):
        """parameters should be None or a dict.
        
        If parameters is a dict, the value for each item in the dict can be
        str, int, float, a instance of some namedtuple, or a iterable contains
        the type just mentioned."""
        if parameters is None:
            parameters = dict()
        else:
            parameters = self._flattenParameters(parameters)
        parameters['Service'] = 'AWSMechanicalTurkRequester'
        parameters['Operation'] = operation
        parameters['Version'] = '2012-03-25'
        parameters['AWSAccessKeyId'] = self.keyId
        parameters['Timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        parameters['Signature'] = self._generateSignature(parameters)

        request = requests.post(self.service_url, params = parameters, verify = self.verify)
        self.respondCache = AMTRespond(request.text)
        print(request.text)
        return self.respondCache

    def GetAccountBalance(self):
        r = self.request('GetAccountBalance')
        if r.valid:
            return float(r['AvailableBalance/Amount'])
    def CreateHIT(self, chp : CreateHITParameters):
        """return (HITId, HITTypeId) or None"""
        r = self.request('CreateHIT', chp.parameters)
        if r.valid:
            return (r['HITId'], r['HITTypeId'])
    def RegisterHITType(self, title, description, rewardAmount, assignmentDurationInSeconds, keywords = None, autoApprovalDelayInSeconds = None, qualificationRequirement = None):
        parameters = {
            'Title'                       : title,
            'Description'                 : description,
            'Reward'                      : sPrice(rewardAmount, 'USD'),
            'AssignmentDurationInSeconds' : assignmentDurationInSeconds,
            'Keywords'                    : keywords,
            'AutoApprovalDelayInSeconds'  : autoApprovalDelayInSeconds,
            'QualificationRequirement'    : qualificationRequirement
        }
        
        r = self.request('RegisterHITType', parameters)
        if r.valid:
            return r['HITTypeId']





class AMTRespond:
    def __init__(self, xml):
        self.xml = xml
        self.root = et.fromstring(self.xml)
        for child in self.root:
            if child.tag == 'OperationRequest':
                self.operationRequest = child
            else:
                self.result = child
        self.error = False
        self.valid = False
        if self.operationRequest.find('Errors'):
            self.error = True
        if self.error == False:
            self.valid = self.result.find('Request/IsValid').text == 'True'

    def _locate(self, element, path):
        r = element.find(path)
        if r != None:
            return r.text
    def locate(self, path):
        return self._locate(self.result, path)
    def __getitem__(self, path):
        return self.locate(path)
    def locateOperationRequest(self, path):
        return self._locate(self.operationRequest, path)
    def locateRoot(self, path):
        return self._locate(self.root, path)

class CreateHITParameters:
    def __init__(self, lifetimeInSeconds, useTypeId = True, useLayoutId = True, maxAssignments = None, assignmentReviewPolicy = None, HITReviewPolicy = None, requesterAnnotation = None, uniqueRequestToken = None):
        self.parameters = {
            'LifetimeInSeconds'      : lifetimeInSeconds,
            'MaxAssignments'         : maxAssignments,
            'AssignmentReviewPolicy' : assignmentReviewPolicy,
            'HITReviewPolicy'        : HITReviewPolicy,
            'RequesterAnnotation'    : requesterAnnotation,
            'UniqueRequestToken'     : uniqueRequestToken,
        }
        self.useTypeId = useTypeId
        self.useLayoutId = useLayoutId
        # block method
        if useTypeId:
            self.setTypeProperties = None
        else:
            self.setTypeId = None
        if useLayoutId:
            self.setQuestion = None
        else:
            self.setLayout = None

    def setTypeId(self, id):
        self.parameters['HITTypeId'] = id
        return self
    def setTypeProperties(self, title, description, rewardAmount, assignmentDurationInSeconds, keywords = None, autoApprovalDelayInSeconds = None, qualificationRequirement = None):
        self.parameters['Title']                       = title
        self.parameters['Description']                 = description
        self.parameters['Reward']                      = sPrice(rewardAmount, 'USD')
        self.parameters['AssignmentDurationInSeconds'] = assignmentDurationInSeconds
        self.parameters['Keywords']                    = keywords
        self.parameters['AutoApprovalDelayInSeconds']  = autoApprovalDelayInSeconds
        self.parameters['QualificationRequirement']    = qualificationRequirement
        return self
    def setQuestion(self, question):
        self.parameters['Question'] = question
        return self
    def setLayout(self, layoutId, layoutParameter : dict):
        """set the layout used and the values for the placeholders
        
        layoutParameter should be a dict whose keys are
        HITLayoutParameter.Name and values are HITLayoutParameter.Value"""
        self.parameters['HITLayoutId'] = layoutId
        self.parameters['HITLayoutParameter'] = [sHITLayoutParameter(k, v) for k, v in layoutParameter.items()]

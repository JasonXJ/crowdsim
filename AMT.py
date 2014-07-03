#!/usr/bin/env python3

import time, hmac, hashlib, base64
import requests
import xml.etree.ElementTree as et
from collections import namedtuple
import logging
import xmltodict

DEBUG = False

sPrice = namedtuple('sPrice', 'Amount, CurrencyCode')
sHITLayoutParameter = namedtuple('sHITLayoutParameter', 'Name, Value')

class flags:
    class sortProperty:
        title = 'Title'
        reward = 'Reward'
        expiration = 'Expiration'
        creationTime = 'CreationTime'
        enumeration = 'Enumeration'

        acceptTime = 'AcceptTime'
        submittime = 'Submittime'
        assignmentStatus = 'AssignmentStatus'

    class sortDirection:
        ascending = 'Ascending'
        descending = 'Descending'

    class responseGroup:
        request = 'Request'
        minimal = 'Minimal'
        hITDetail = 'HITDetail'
        hITQuestion = 'HITQuestion'
        hITAssignmentSummary = 'HITAssignmentSummary'
        parameters = 'Parameters'
        assignmentFeedback = 'AssignmentFeedback'

    class status:
        reviewable = 'Reviewable'
        reviewing = 'Reviewing'

    class assignmentStatus:
        submitted = 'Submitted'
        approved = 'Approved'
        rejected = 'Rejected'
        approvedOrRejected = 'Approved,Rejected'

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
        if DEBUG:
            from xml.dom.minidom import parseString
            logging.debug('request url: ' + request.url)
            logging.debug('respond text:\n' + parseString(request.text).toprettyxml())
        self.respondCache = AMTRespond(request.text)
        return self.respondCache

    def getAccountBalance(self):
        r = self.request('GetAccountBalance')
        if r.valid:
            return float(r['AvailableBalance/Amount'])

    def createHIT(self, createHITParameters):
        """CreateHIT based on createHITParameters, which should be of type "CreateHITParameters"
        
        return (HITId, HITTypeId) or None"""
        r = self.request('CreateHIT', createHITParameters.parameters)
        if r.valid:
            return (r['HITId'], r['HITTypeId'])

    def registerHITType(self, title, description, rewardAmount, assignmentDurationInSeconds, keywords = None, autoApprovalDelayInSeconds = None, qualificationRequirement = None):
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

    def _extractComplexResultsToDict(self, dest, responseXml, extractFunc, idExtractFunc = None):
        def addInDest(item):
            if idExtractFunc is None:
                dest.append(item)
            else:
                id = idExtractFunc(item) 
                if id not in idSet:
                    idSet.add(id)
                    dest.append(item)

        d = xmltodict.parse(responseXml, dict_constructor = dict)
        idSet = set()
        targetList = extractFunc(d)
        if not isinstance(targetList, list):
            # is an item instead of a list
            addInDest(targetList)
        else:
            for item in targetList:
                addInDest(item)

    def getReviewableHITs(self, HITTypeId = None, status : flags.status = None,
            sortProperty : flags.sortProperty = None, sortDirection :
            flags.sortDirection = None, pageSize = None, pageNumber = None):
        """Retrieve HITs and return a list of deduplicated HITId (order does not change)"""

        getAllPages = False
        if pageNumber is None:
            pageNumber = 1
            getAllPages = True

        parameters = {
            'HITTypeId'     : HITTypeId,
            'Status'        : status,
            'SortProperty'  : sortProperty,
            'SortDirection' : sortDirection,
            'PageSize'      : pageSize,
            'PageNumber'    : pageNumber,
        }
        idSet = set()
        idList = []

        while True:
            r = self.request('GetReviewableHITs', parameters)
            if not r.valid:
                return
            if int(r['NumResults']) == 0:
                break
            for x in r.result.findall('HIT'):
                id = x.find('HITId').text
                if id not in idSet:
                    idSet.add(id)
                    idList.append(id)
            if getAllPages == False:
                break
            parameters['PageNumber'] += 1
        return idList

    def getAssignmentsForHIT(self, id, assignmentStatus : flags.assignmentStatus = None, sortProperty : flags.sortProperty = None, sortDirection : flags.sortDirection = None, pageSize = None, pageNumber = None):
        """@todo: Docstring for getAssignmentsForHIT.

        :arg1: @todo
        :returns: @todo

        """
        pass

    def searchHITs(self, sortProperty : flags.sortProperty = None,
            sortDirection : flags.sortDirection = None, pageNumber = None,
            pageSize = None, responseGroup : flags.responseGroup = None):
        """Retrieve HITs and return a deduplicated list of dict

        Each element of the list is a dict that represent an HIT. The list has
        been deduplicated based on the HITId but the order does not change.

        If one of the respond from AMT is not valid, the return value will be None

        If pageNumber == None, then this function will retrieve pages from page
        1 until no results are returned."""

        getAllPages = False
        if pageNumber is None:
            pageNumber = 1
            getAllPages = True
        parameters = {
            'SortProperty'  : sortProperty,
            'SortDirection' : sortDirection,
            'PageNumber'    : pageNumber,
            'PageSize'      : pageSize,
            'ResponseGroup' : responseGroup
        }
        dictList = []
        while True:
            r = self.request('SearchHITs', parameters)
            if not r.valid:
                return
            if int(r['NumResults']) == 0:
                break
            self._extractComplexResultsToDict(dictList, r.xml,
                    lambda x: x['SearchHITsResponse']['SearchHITsResult']['HIT'], lambda x : x['HITId'])
            if getAllPages == False:
                break
            parameters['PageNumber'] += 1
        return dictList

    def disposeHIT(self, id): 
        r = self.request('DisposeHIT', {'HITId', id})
        return r.valid

    def disableHIT(self, id): 
        r = self.request('DisableHIT', {'HITId', id})
        return r.valid

    def forceExpireHIT(self, id):
        r = self.request('ForceExpireHIT', {'HITId', id})
        return r.valid

    def extendHIT(self, id, maxAssignmentsIncrement = None, expirationIncrementInSeconds = None, uniqueRequestToken = None):
        parameters = {
            'HITId'                           : id,
            'MaxAssignmentsIncrement'      : maxAssignmentsIncrement,
            'ExpirationIncrementInSeconds' : expirationIncrementInSeconds,
            'UniqueRequestToken'           : uniqueRequestToken,
        }
        r = self.request('ExtendHIT', parameters)
        return r.valid

    def _setHITAsReviewing(self, id, revert):
        '''Don't use this function directly. Use toReviewing()/toReviewable()'''
        r = self.request('SetHITAsReviewing', {'HITId' : id, 'Revert' : revert})
        return r.valid
    def toReviewing(self, id):
        return self._setHITAsReviewing(id, revert = 'false')
    def toReviewable(self, id):
        return self._setHITAsReviewing(id, revert = 'true')


class AMTRespond:
    def __init__(self, xml):
        self.xml = xml
        self.root = et.fromstring(self.xml)
        for child in self.root:
            if child.tag == 'OperationRequest':
                self.operationRequest = child
            else:
                self.result = child

        self.valid = False
        if self.result is not None:
            validElement = self.result.find('Request/IsValid')
            if validElement is not None and validElement.text == 'True':
                self.valid = True

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

    def setLayout(self, layoutId, layoutParameter : dict = None):
        """set the layout used and the values for the placeholders
        
        layoutParameter should be a dict whose keys are
        HITLayoutParameter.Name and values are HITLayoutParameter.Value"""
        self.parameters['HITLayoutId'] = layoutId
        if layoutParameter != None:
            self.parameters['HITLayoutParameter'] = [sHITLayoutParameter(k, v) for k, v in layoutParameter.items()]
        return self

    def setLayoutParameter(self, layoutParameter : dict):
        self.parameters['HITLayoutParameter'] = [sHITLayoutParameter(k, v) for k, v in layoutParameter.items()]
        return self

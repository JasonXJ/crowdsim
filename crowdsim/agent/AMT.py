#!/usr/bin/env python3

import time, hmac, hashlib, base64
import requests
import xml.etree.ElementTree as et
from collections import namedtuple
import logging
import xmltodict
import xml.dom.minidom as minidom
import xml.parsers.expat.errors as xmlErrors
from xml.parsers.expat import ExpatError
import uuid

DEBUG = False

sPrice = namedtuple('sPrice', 'Amount, CurrencyCode')
sHITLayoutParameter = namedtuple('sHITLayoutParameter', 'Name, Value')

class TimeUnit:
    minute = 60
    hour = 60 * minute
    day = 24 * hour
    week = 7 * day
    month = 30 * day

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
        hitDetail = 'HITDetail'
        hitQuestion = 'HITQuestion'
        hitAssignmentSummary = 'HITAssignmentSummary'
        parameters = 'Parameters'
        assignmentFeedback = 'AssignmentFeedback'

    class status:
        reviewable = 'Reviewable'
        reviewing = 'Reviewing'

    class assignmentStatus:
        submitted = 'Submitted'
        approved = 'Approved'
        rejected = 'Rejected'
        #approvedOrRejected = [Approved,Rejected]

class AMT:
    def __init__(self, keyId, secret, useSandbox = True, verify = True, timeout = 5.0, tries = 5, uuidGenerator = uuid.uuid1):
        '''Init...

        `timeout` will be passed to requests.post() and `tries` indicate
        the maximal times to call the post() method when encounter Timeout
        exceptions.

        uuidGenerator will be used for createHIT() and extendHIT()'''

        self.keyId = keyId
        self.bSecret = secret.encode('utf-8')
        self.verify = verify
        self.timeout = timeout
        self.tries = tries
        self.uuidGenerator = lambda : str(uuidGenerator())
        if useSandbox:
            self.service_url='https://mechanicalturk.sandbox.amazonaws.com/'
        else:
            self.service_url='https://mechanicalturk.amazonaws.com/'

    def request(self, operation, parameters = None, addUuid = False):
        """parameters should be None or a dict. Return (AMTRespond, multipleRequest)

        multipleRequest == True if the requests.post() has been called multiple
        times because of timeout.
        
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
        if addUuid:
            self.uuidCache = parameters['UniqueRequestToken'] = self.uuidGenerator()
        else:
            self.uuidCache = None

        for tryTimes in range(self.tries):
            try:
                request = requests.post(self.service_url, params = parameters, verify = self.verify, timeout = self.timeout)
            except requests.Timeout:
                logging.warning('Requests timeout: #{}'.format(tryTimes + 1))
                continue
            break
        if DEBUG:
            logging.debug('request url: ' + request.url)
            logging.debug('respond text:\n' + minidom.parseString(request.text).toprettyxml())
        self.respondCache = AMTRespond(request.text)
        return (self.respondCache, tryTimes > 1)

    def getAccountBalance(self):
        r = self.request('GetAccountBalance')[0]
        if r.valid:
            return float(r['AvailableBalance/Amount'])

    def createHIT(self, HITParameters):
        """CreateHIT based on HITParameters, which should be of type "HITParameters"
        
        return (HITId, HITTypeId) or None"""
        self.HITAlreadyExists = False
        r, multipleRequest = self.request('CreateHIT', HITParameters.parameters, addUuid = True)
        if r.valid:
            return (r['HITId'], r['HITTypeId'])
        elif multipleRequest:
            code = self.respondCache.result.findtext('Request/Errors/Error/Code')
            if code == "AWS.MechanicalTurk.HITAlreadyExists":
                # if this happen, the hit is actuall created successfully, but
                # r.valud == False because of multiple CreateHIT operation with
                # the same uuid
                self.HITAlreadyExists = True
                logging.warning('creatHIT encounters error "HITAlreadExists"')
                for element in self.respondCache.result.findall('Request/Errors/Error/Data'):
                    if element.findtext('Key') == 'HITId':
                        hitId = element.findtext('Value')
                        if hitId is not None:
                            break
                else:
                    raise RuntimeError('Cannot get HITId')
                r = self.getHIT(hitId, responseGroup = flags.responseGroup.minimal)
                typeId = r.findtext('HITTypeId')
                if typeId is None:
                    raise RuntimeError('Cannot get HITTypeId')
                return (hitId, typeId)

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
        
        r = self.request('RegisterHITType', parameters)[0]
        if r.valid:
            return r['HITTypeId']

    def getReviewableHITs(self, HITTypeId = None, status : flags.status = None,
            sortProperty : flags.sortProperty = None, sortDirection :
            flags.sortDirection = None, pageSize = None, pageNumber = None):
        """Retrieve HITs and return a list of deduplicated HITId
        
        see _getPages() for more help"""
        parameters = {
            'HITTypeId'     : HITTypeId,
            'Status'        : status,
            'SortProperty'  : sortProperty,
            'SortDirection' : sortDirection,
            'PageSize'      : pageSize,
            'PageNumber'    : pageNumber,
        }
        return self._getPages('GetReviewableHITs', parameters, lambda x :
                x.findall('HIT'), lambda x : x.findtext('HITId'), lambda i, e: i)

    def getAssignmentsForHIT(self, id, assignmentStatus :
            flags.assignmentStatus = None, sortProperty : flags.sortProperty =
            None, sortDirection : flags.sortDirection = None, pageSize = None,
            pageNumber = None):
        '''Retrieve and return a deduplicated list of tuples (assignmentId, answer, assignment)

        The `assignment` is an xml elements and the `answer` is a dict which is
        extracted by self._answerDictConstructor()
        
        see _getPages() for more help'''

        parameters = {
            'HITId'            : id,
            'AssignmentStatus' : assignmentStatus,
            'SortProperty'     : sortProperty,
            'SortDirection'    : sortDirection,
            'PageSize'         : pageSize,
            'PageNumber'       : pageNumber,
        }
        
        def constructTuple(id, element):
            answerString = element.findtext('Answer')
            answer = None
            if answerString is not None:
                answer = self._answerDictConstructor(answerString)
            return (id, answer, element)

        return self._getPages('GetAssignmentsForHIT', parameters, lambda r :
                r.findall('Assignment'), lambda e : e.findtext('AssignmentId'),
                constructTuple)

    def searchHITs(self, sortProperty : flags.sortProperty = None,
            sortDirection : flags.sortDirection = None, pageNumber = None,
            pageSize = None, responseGroup : flags.responseGroup = None):
        """Retrieve HITs and return a deduplicated list of HIT xml element

        See _getPages() for more help"""

        parameters = {
            'SortProperty'  : sortProperty,
            'SortDirection' : sortDirection,
            'PageNumber'    : pageNumber,
            'PageSize'      : pageSize,
            'ResponseGroup' : responseGroup
        }
        return self._getPages('SearchHITs', parameters, lambda x : x.findall('HIT'),
                lambda x : x.findtext('HITId'), lambda i, e : e)

    def disposeHIT(self, id): 
        r = self.request('DisposeHIT', {'HITId': id})[0]
        return r.valid

    def disableHIT(self, id): 
        r = self.request('DisableHIT', {'HITId': id})[0]
        return r.valid

    def forceExpireHIT(self, id):
        r = self.request('ForceExpireHIT', {'HITId': id})[0]
        return r.valid

    def extendHIT(self, id, maxAssignmentsIncrement = None, expirationIncrementInSeconds = None):
        parameters = {
            'HITId'                           : id,
            'MaxAssignmentsIncrement'      : maxAssignmentsIncrement,
            'ExpirationIncrementInSeconds' : expirationIncrementInSeconds,
        }
        r, multipleRequest = self.request('ExtendHIT', parameters, addUuid = True)
        self.duplicateExtendHIT = False
        if r.valid:
            return r.valid
        if multipleRequest:
            code = r.result.findtext('Request/Errors/Error/Code')
            if code == 'AWS.MechanicalTurk.DuplicateCall':
                logging.warning('extendHIT encounters error "DuplicateCall"')
                self.duplicateExtendHIT = True
                return True
        return False

    def toReviewing(self, id):
        return self._setHITAsReviewing(id, revert = 'false')
    def toReviewable(self, id):
        return self._setHITAsReviewing(id, revert = 'true')

    def approveAssignment(self, assignmentId, requesterFeedback = None):
        parameters = {
            'AssignmentId'      : assignmentId,
            'RequesterFeedback' : requesterFeedback,
        }
        return self.request('ApproveAssignment', parameters)[0].valid

    def rejectAssignment(self, assignmentId, requesterFeedback = None):
        parameters = {
            'AssignmentId'      : assignmentId,
            'RequesterFeedback' : requesterFeedback,
        }
        return self.request('RejectAssignment', parameters)[0].valid

    def getHIT(self, id, responseGroup : flags.responseGroup = None):
        r = self.request('GetHIT', {'HITId' : id, 'ResponseGroup' : responseGroup})[0]
        return r.result

    def _answerDictConstructor(self, answerString):
        '''Construct a dict represent the answer based on the xml answerString

        This function parse the xml and return a dict based on the xsd
        (http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/QuestionFormAnswers.xsd).
        except that it assumes there is exactly one 'Answer' element.

        If no element found in answerString, it returns None.'''

        namespaces = {'http://mechanicalturk.amazonaws.com/'\
                'AWSMechanicalTurkDataSchemas/2005-10-01/QuestionFormAnswers.xsd' : None}
        # TODO: the 0.9.0 version of xmltodict cannot deal with namespaces
        # correctly. While this function works correctly now, the lack of
        # namespaces support may suppress some errors. Check xmltodict when the
        # new version is published.
        try:
            d = xmltodict.parse(answerString, namespaces = namespaces, dict_constructor=dict)
        except ExpatError as err:
            if xmlErrors.messages[err.code] == xmlErrors.XML_ERROR_NO_ELEMENTS:
                return
            raise

        self.origind = d
        d = d['QuestionFormAnswers']['Answer']
        if isinstance(d, list):
            raise RuntimeError('Multiple "answer" elements!')
        if 'SelectionIdentifier' in d and not isinstance(d['SelectionIdentifier'], list):
            # This element can appear multiple times. Make sure it is always a
            # list.
            d['SelectionIdentifier'] = [d['SelectionIdentifier']]
        return d

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

    def _getPages(self, operation, param : dict, elementExtracter : callable, idExtracter : callable, handler : callable):
        '''A common function for API that retrieve data based on page number.

        If one of the respond is invalid or idExtracter() return None, the
        return value will be None.
        
        If param["PageNumber"] is None, then this function will get pages 1, 2
        ... until int(response['NumResults']) == 0. Elements with smaller page
        numbers will appear first.
        
        elementExtracter(AMTRespond.result) is a callable object that return
        iterable for interesting elements.
        
        idExtracter(element) is a callable object that extract id from elements.
        The returned list is deduplicated based on the id.

        handler(id, element) is a callable object that return a value to be
        appended to the returned list.'''

        getAllPages = False
        if param['PageNumber'] is None:
            param['PageNumber'] = 1
            getAllPages = True
        returnList = []
        idSet = set()
        while True:
            r = self.request(operation, param)[0]
            if not r.valid:
                return
            if int(r['NumResults']) == 0:
                break
            for element in elementExtracter(r.result):
                id = idExtracter(element)
                assert(id is not None)
                if id not in idSet:
                    idSet.add(id)
                    returnList.append(handler(id, element))
            if getAllPages == False:
                break
            param['PageNumber'] += 1
        return returnList

    def _setHITAsReviewing(self, id, revert):
        '''Don't use this function directly. Use toReviewing()/toReviewable()'''
        r = self.request('SetHITAsReviewing', {'HITId' : id, 'Revert' : revert})[0]
        return r.valid




class AMTRespond:
    def __init__(self, xml):
        self.xml = xml
        self.root = et.fromstring(self.xml)
        self.operationRequest = self.result = None
        for child in self.root:
            if child.tag == 'OperationRequest':
                self.operationRequest = child
            else:
                self.result = child

        self.error = False
        for item in self.root.iter():
            if item.tag == 'Errors' or item.tag == 'Error':
                self.error = True
                break

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

class HITParameters:
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

def xmlPrettyPrint(source):
    """A function to print xml element / string"""
    if isinstance(source, et.Element):
        string = et.tostring(source, 'utf-8')
    else:
        string = source
    print(minidom.parseString(string).toprettyxml())

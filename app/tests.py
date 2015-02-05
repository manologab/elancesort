from django.test import TestCase
from django.test.client import Client
import json
import copy

#test data
TEST_DATA = {
    'toSort' :[{'d': '01:06:2015', 'originalOrder': 1, 'p': 250, 'r': 1},
               {'d': '15:06:2015', 'originalOrder': 2, 'p': 200, 'r': 2},
               {'d': '02:06:2015', 'originalOrder': 3, 'p': 100, 'r': 2}],
    'dPriority': 1,
    'pPriority': 5,
    'rPriority': 4
}
    

class RequestError(Exception):
    """
    Request error
    """
    def __init__(self, response):
        if response['Content-Type'] == 'application/json':
            jsonResp = json.loads(response.content.decode('utf-8', 'replace'))
            msg = jsonResp['error']
        else:
            msg = '%d %s'%(response.status_code, response.reason_phrase)
        super(RequestError, self).__init__(msg)
        

def jsonRequest(data, client = None):
    """
    Perform a simple request
    """
    if client is None:
        client = Client()
    
    data = {} if data is None else {'json': json.dumps(data)}

    resp = client.get('/', data)

    if resp.status_code != 200:
        raise RequestError(resp)
        
    return json.loads(resp.content.decode('utf-8', 'replace'))

class MainTest(TestCase):
    def test_notFound(self):
        c = Client()
        resp = c.get('/notfound')
        self.assertEqual(resp.status_code, 404)

    def test_validation(self):
        with self.assertRaisesRegexp(RequestError, 'data not received'):
            jsonRequest(None);

        with self.assertRaisesRegexp(RequestError, 'invalid data'):
            jsonRequest('xxx');

        for k in ['toSort', 'dPriority', 'pPriority', 'rPriority']:
            data = copy.deepcopy(TEST_DATA)
            del(data[k])
            with self.assertRaisesRegexp(RequestError, 'key not found:'+k):
                jsonRequest(data);
        
        data = copy.deepcopy(TEST_DATA)
        data['dPriority'] = 'a'    
        with self.assertRaisesRegexp(RequestError, 'Priorities must be integers'):
            jsonRequest(data);

        data = copy.deepcopy(TEST_DATA)
        data['pPriority'] = -3
        with self.assertRaisesRegexp(RequestError, 'Priorities must be >= 0'):
            jsonRequest(data);

        data = copy.deepcopy(TEST_DATA)
        data['toSort'] = 'xx'
        with self.assertRaisesRegexp(RequestError, 'must be a list of objects'):
            jsonRequest(data);

        for k in ['d', 'p', 'r']:
            data = copy.deepcopy(TEST_DATA)
            del(data['toSort'][0][k])
            with self.assertRaisesRegexp(RequestError, 'key not found:'+k):
                jsonRequest(data);

        data = copy.deepcopy(TEST_DATA)
        data['toSort'][0]['d'] = 'xxx'
        with self.assertRaisesRegexp(RequestError, 'invalid value'):
            jsonRequest(data);

        data = copy.deepcopy(TEST_DATA)
        data['toSort'][0]['d'] = '22:06:2015'
        with self.assertRaisesRegexp(RequestError, '"d" must be between '):
            jsonRequest(data);

        data = copy.deepcopy(TEST_DATA)
        data['toSort'][0]['p'] = 'xxx'
        with self.assertRaisesRegexp(RequestError, 'must be integers'):
            jsonRequest(data);

        data = copy.deepcopy(TEST_DATA)
        data['toSort'][0]['p'] = 40
        with self.assertRaisesRegexp(RequestError, 'value of "p" must be '):
            jsonRequest(data);

        data = copy.deepcopy(TEST_DATA)
        data['toSort'][0]['r'] = 5
        with self.assertRaisesRegexp(RequestError, 'value of "r" must be '):
            jsonRequest(data);
                
        
    def test_normal(self):
        """
        Main test
        """
        data = copy.deepcopy(TEST_DATA)
        sortedData = jsonRequest(data)
        self.assertEquals(sortedData[0]['originalOrder'], 3)
        self.assertEquals(sortedData[1]['originalOrder'], 1)
        self.assertEquals(sortedData[2]['originalOrder'], 2)
        
        
    def test_onlyP(self):
        """
        Order by P only
        """
        data = {
            'toSort' :[{'d': '01:06:2015', 'originalOrder': 1, 'p': 250, 'r': 1},
                       {'d': '15:06:2015', 'originalOrder': 2, 'p': 200, 'r': 2},
                       {'d': '02:06:2015', 'originalOrder': 3, 'p': 100, 'r': 2}],
            'dPriority': 0,
            'pPriority': 1,
            'rPriority': 0
        }
        sortedData = jsonRequest(data)
        self.assertEquals(sortedData[0]['originalOrder'], 3)
        self.assertEquals(sortedData[1]['originalOrder'], 2)
        self.assertEquals(sortedData[2]['originalOrder'], 1)

    def test_onlyD(self):
        """
        Order by D only
        """
        data = {
            'toSort' :[{'d': '01:06:2015', 'originalOrder': 1, 'p': 250, 'r': 1},
                       {'d': '15:06:2015', 'originalOrder': 2, 'p': 200, 'r': 2},
                       {'d': '02:06:2015', 'originalOrder': 3, 'p': 100, 'r': 2}],
            'dPriority': 5,
            'pPriority': 0,
            'rPriority': 0
        }
        sortedData = jsonRequest(data)
        self.assertEquals(sortedData[0]['originalOrder'], 1)
        self.assertEquals(sortedData[1]['originalOrder'], 3)
        self.assertEquals(sortedData[2]['originalOrder'], 2)


    def test_onlyR(self):
        """
        Order by r, items keep their position when equals
        """
        data = {
            'toSort' :[{'d': '01:06:2015', 'originalOrder': 1, 'p': 250, 'r': 1},
                       {'d': '15:06:2015', 'originalOrder': 2, 'p': 200, 'r': 2},
                       {'d': '02:06:2015', 'originalOrder': 3, 'p': 100, 'r': 2}],
            'dPriority': 0,
            'pPriority': 0,
            'rPriority': 1
        }
        sortedData = jsonRequest(data)
        self.assertEquals(sortedData[0]['originalOrder'], 1)
        self.assertEquals(sortedData[1]['originalOrder'], 2)
        self.assertEquals(sortedData[2]['originalOrder'], 3)

        

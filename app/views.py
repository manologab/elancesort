from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
import json
import re
# Create your views here.

def error(msg):
    """
    Return a json error
    """
    resp = {'error': msg}
    return HttpResponseBadRequest(json.dumps(resp), content_type='application/json')


def validateInput(data):
    """
    Validate input received, raise ValueError for invalid input
    """
    if not isinstance(data, dict):
        raise ValueError('invalid data')

    try:
        toSort = data['toSort']
        dPriority = int(data['dPriority'])
        pPriority = int(data['pPriority'])
        rPriority = int(data['rPriority'])
    except KeyError as e:
        raise ValueError("required key not found:" + e.args[0])
    except ValueError as e:
        raise ValueError("Priorities must be integers")
    
    if dPriority <0 or pPriority < 0 or rPriority < 0:
        raise ValueError("Priorities must be >= 0")

    
    for item in toSort:
        if not isinstance(item, dict):
            raise ValueError('"toSort" must be a list of objects')
        try:
            d = item['d']
            p = int(item['p'])
            r = int(item['r'])
        except KeyError as e:
            raise ValueError('key not found:' + e.args[0])
        except ValueError as e:
            raise ValueError('"p" and "r" must be integers')

        #only dates(?) from 01:06:2015 to 15:06:2015 allowed
        mt = re.match('(\d\d):06:2015', d)
        if mt:
            dInt = int(mt.group(1))
            if dInt < 1 or dInt > 15:
                raise ValueError('"d" must be between "01:06:2015" and "15:06:2015"')
        else:
            raise ValueError('invalid value for "d":'+d)

        if p < 100 or p > 250:
            raise ValueError('value of "p" must be between 100 and 250')
        if r < 1 or r > 2:
            raise ValueError('value of "r" must be 1 or 2')

    return (toSort, dPriority, pPriority, rPriority)


def normalize5(value, minValue, maxValue):
    """
    Normalize a given value between -5 and 5
    """
    return ((10.0/(maxValue - minValue)) * (value - minValue)) - 5.0
    

def qualifyItem(item, dPrio, pPrio, rPrio):
    """
    Qualify an item for the given priorities, dPrio, pPrio an rPrio must be normalized between 0 and 1
    """
    #normalize the values to [-5..5]
    d = normalize5(int(item['d'][:2]), 1, 15)
    p = normalize5(int(item['p']), 100, 250)
    r = normalize5(int(item['r']), 1, 2)

    #in order to apply priorities we need to move the range to positive values [0..10)
    #using this logic it would have been better to normalize the values to [0..1]
    # given that the normalized5 values are not used for anything else
    d = (d + 5) * dPrio
    p = (p + 5) * pPrio
    r = (r + 5) * rPrio

    return d + p +r
    
    
    

def main(request):
    try: 
        dataRaw = request.GET['json']
    except KeyError:
        return error('data not received')

    try:
        data = json.loads(dataRaw)
    except ValueError:
        return error('invalid data')

    try:
        (toSort, dPriority, pPriority, rPriority) = validateInput(data)
    except ValueError as e:
        return error(e.args[0])

    #normalize priorities to [0..1]
    sumPrios = float(dPriority + pPriority + rPriority)
    dPriority = dPriority/sumPrios
    pPriority = pPriority/sumPrios
    rPriority = rPriority/sumPrios

    sortedItems = sorted(toSort, key=lambda i: qualifyItem(i, dPriority, pPriority, rPriority))

    return HttpResponse(json.dumps(sortedItems), content_type='application/json')

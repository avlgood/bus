#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)

@app.route('/bus', methods=['POST'])
def bus():
    req = request.get_json(silent=True, force=True)
    print("Request:")
    print(json.dumps(req, indent=4))

    if req.get("result").get("action") != "schedule":
        return {}
    
    schedules = ["6:40", "7:20", "7:45", "8:10", "8:35", "9:00", "9:30", "15:56", "16:15", "16:39", "16:55",
                "17:27", "17:55", "18:35", "19:05", "20:20", "21:05"]
    print("Enter 1")
    current_time = req.get("result").get("parameters").get("time")
    result = getResult(current_time)
    print("Exit 1: ", result)
    result = json.dumps(result, indent=4)
    r = make_response(result)
    r.headers['Content-Type'] = 'application/json'
    print("Enter 2")
    return r 


def getResult(curTime):
    schedules = ["6:40", "7:20", "7:45", "8:10", "8:35", "9:00", "9:30", "15:56", "16:15", "16:39", "16:55",
                "17:27", "17:55", "18:35", "19:05", "20:20", "21:05"]

    print("Current time" + curTime)
    (h, m, s) = curTime.split(':')
    nextTime = ""
    for t in schedules:
        print("Enter 2, t = " + t)
        (h1, m1) = t.split(':')
        if h1 > h:
            nextTime = t
        elif m1 > m:
            nextTime = t
            
    speech = "Current time is: " + curTime + ". Sorry Zhaoyan, there's no more shuttles, you have to call Uber."
    if nextTime:
        speech = "Current time is: " + curTime +  "Congrats Zhaoyan! Your next bus will arrive at " +  nextTime + ", have a nice trip!"

    print("Response:")
    print(speech)

    result = {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }
    

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    if req.get("result").get("action") != "yahooWeatherForecast":
        return {}
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = makeYqlQuery(req)
    if yql_query is None:
        return {}
    yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
    result = urlopen(yql_url).read()
    data = json.loads(result)
    res = makeWebhookResult(data)
    return res


def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"


def makeWebhookResult(data):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = "Hello Zhaoyan! Today in " + location.get('city') + ": " + condition.get('text') + \
             ", the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')

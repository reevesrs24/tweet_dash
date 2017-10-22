from django.shortcuts import render, redirect
from django.http import HttpResponse
from firebase import firebase
import time
import datetime

def index(request):
    f = firebase.FirebaseApplication('https://tweet-dash.firebaseio.com', None)
    result = f.get('/tweet-dash', None)
    tweets = []
    for res in result.values():
      timestamp = time.mktime(time.strptime(res['date'], '%Y-%m-%d %H:%M:%S'))
      res['date'] = timestamp
      tweets.append(res)
    tweets.sort(key=lambda x: x['date'], reverse=True)
    for tweet in tweets:
      tweet['day'] = datetime.datetime.fromtimestamp(int(tweet['date'])).strftime("%A")
      date = datetime.datetime.fromtimestamp(int(tweet['date'])).strftime('%Y-%m-%d %H:%M:%S')
      tweet['date'] = date
    return render(request, 'index.html', {'tweets': tweets})
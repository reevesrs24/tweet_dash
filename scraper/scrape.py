#!/usr/bin/env python
# encoding: utf-8

import tweepy #https://github.com/tweepy/tweepy
import csv
import json
from bs4 import BeautifulSoup
import urllib2
import re

from firebase import firebase

THRESHOLD = 100
TWITTER_USER = "AJA_Cortes"

#Twitter API credentials
consumer_key = "BCzFkHKVKhecVmI06PRFnKAZI"
consumer_secret = "lJrHlW9ADqj0IkGDagD5cL1BRSYPtOn4ElNgiP8MDwGsrhYOeU"
access_key = "2647059338-TSbrq91lisRMU1Bv19QaXETVQR0b8SjhZlQe7QW"
access_secret = "cNTAITeVRtvKiIl8OpwL9mV9hdeKggxbn4XA4PYrsrC1D"


# bulk of the code for this function came from https://gist.github.com/yanofsky/5436496
def get_all_tweets(screen_name):
	#Twitter only allows access to a users most recent 3240 tweets with this method

	#authorize twitter, initialize tweepy
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_key, access_secret)
	api = tweepy.API(auth)

	#initialize a list to hold all the tweepy Tweets
	alltweets = []

	#make initial request for most recent tweets (200 is the maximum allowed count)
	new_tweets = api.user_timeline(screen_name = screen_name, count=200)

	#save most recent tweets
	alltweets.extend(new_tweets)

	#save the id of the oldest tweet less one
	oldest = alltweets[-1].id - 1

	#keep grabbing tweets until there are no tweets left to grab
	while len(new_tweets) > 0:
		print "getting tweets before %s" % (oldest)

		#all subsiquent requests use the max_id param to prevent duplicates
		new_tweets = api.user_timeline(screen_name = screen_name, count=200, max_id=oldest)

		#save most recent tweets
		alltweets.extend(new_tweets)

		#update the id of the oldest tweet less one
		oldest = alltweets[-1].id - 1

		print "...%s tweets downloaded so far" % (len(alltweets))

	#transform the tweepy tweets into a 2D array that will populate the csv
	outtweets = [[tweet.id_str, tweet.created_at, tweet.favorite_count, tweet.retweet_count, tweet.in_reply_to_status_id_str, tweet.text.encode("utf-8")] for tweet in alltweets]

	return outtweets
	'''
	#write the csv
	with open('%s_tweets.csv' % screen_name, 'wb') as f:
		writer = csv.writer(f)
		writer.writerow(["id","created_at", "favorite_count", "retweet_count", "in_reply_to_status_id_str", "text"])
		writer.writerows(outtweets)
	pass
	'''

#grab tweets with >100 likes
def curate_popular_tweets(tweet_list):
	popular_leading_tweets = []
	for tweet in tweet_list[1:]:
		print "in_reply_to_status_id_str is: %s" % (tweet[4])
		print "type of in_reply_to_status_id_str is: %s" % (type(tweet[4]))
		if int(tweet[2]) >= THRESHOLD and tweet[4] == None:
			popular_leading_tweets.append(tweet)

	'''
	#write the csv
	with open('popular_leading_tweets.csv', 'wb') as f:
		writer = csv.writer(f)
		writer.writerow(["id","created_at", "favorite_count", "retweet_count", "in_reply_to_status_id_str", "text"])
		writer.writerows(popular_leading_tweets)
	'''

	print "There are %s popular threads (leading tweets)" % (len(popular_leading_tweets))

	return popular_leading_tweets

# get the entire thread led by the "leading tweet"
def get_thread(tweet_id):
	response = urllib2.urlopen('https://twitter.com/AJA_Cortes/status/' + str(tweet_id))
	html = response.read()
	soup = BeautifulSoup(html, 'html.parser')
	names = soup.findAll('span', { 'class' : 'FullNameGroup' })
	sub_tweets = soup.findAll('p', { 'class' : 'tweet-text' })

	name_tweet_pairs = []
	for i in range(0, len(names)):
		name = re.sub('[^A-Za-z0-9\s.]+', '', names[i].getText())
		name = name.replace("\n", '')
		if (name == 'Alexander J.A Cortes'):
		# get pairs of (name, tweet)
			pair = (name, sub_tweets[i].getText())
			name_tweet_pairs.append(pair)

	# Convert from [(name, tweet), ...] to [tweet_1, tweet_2, ...]
	tweets = []
	for pair in name_tweet_pairs:
		tweets.append(pair[1])

	return tweets

def get_thread_dictionary(popular_leading_tweet_list):
	list_of_thread_dictionaries = [] # list of dictionaries
	i = 1

	# Wrap each thread into a dictionary (object) with relevant info (date, likes, etc)
	# and dump it into a list
	for leading_tweet in popular_leading_tweet_list:
		thread_dictionary = {}
		thread_dictionary["id"] = int(leading_tweet[0])
		thread_dictionary["leading_tweet"] = leading_tweet[5]
		thread_dictionary["date"] = leading_tweet[1]
		thread_dictionary["likes"] = int(leading_tweet[2])
		thread_dictionary["retweets"] = int(leading_tweet[3])

		print "Processing the %sth thread..." % (i)
		i += 1

		thread_dictionary["thread"] = get_thread(int(leading_tweet[0]))

		list_of_thread_dictionaries.append(thread_dictionary)

	return list_of_thread_dictionaries

config = {
   	"apiKey": "AIzaSyBf_SnNvao1l5sFOtE_pmvaQ5Jzaq7OuYc",
    "authDomain": "tweet-dash.firebaseapp.com",
    "databaseURL": "https://tweet-dash.firebaseio.com",
    "projectId": "tweet-dash",
    "storageBucket": "tweet-dash.appspot.com",
    "messagingSenderId": "795758646517"
}

def postToDatabase(list_of_threads):
	f = firebase.FirebaseApplication('https://tweet-dash.firebaseio.com', None)
	#f = firebase.FirebaseApplication('https://lambda-test-5b64e.firebaseio.com', None)

	i = 1
	for thread_object in list_of_threads:
		print "Posting the %sth object up on Firebase..." % (i)
		i += 1
		f.post('/fun', thread_object)
	#result = f.get('/tweet-dash', None)
	#print result




def main(event, context):
	#pass in the username of the account you want to download
	tweet_list = get_all_tweets(TWITTER_USER)

	popular_leading_tweet_list = curate_popular_tweets(tweet_list)

	list_of_thread_dictionaries = get_thread_dictionary(popular_leading_tweet_list)

	postToDatabase(list_of_thread_dictionaries)

if __name__ == "__main__":
    main({}, "What")


import os
import pandas as pd
import json
import tweepy as tp
import csv
from flask import Flask, render_template, request, jsonify, make_response
from textblob import TextBlob

from twitter_auth import API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import ast

from tweepy import Stream
from tweepy.streaming import StreamListener

auth = tp.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tp.API(auth)
app = Flask(__name__)

allTweets = []
arrayTweets = []

@app.route('/')
def home():
    return render_template('home.html')


# ****************** static data showcase ******************
@app.route('/textblobVader')
def getStaticTweets():
    tweetCount = 100
    allTweets = tp.Cursor(api.search, q="trump", lang="en").items(tweetCount)
    # allTweets = tp.Cursor(api.search, q="trump -filter:retweets", lang="en").items(tweetCount)

    outputFile = open('static/CSV/output.csv', 'a')
    fileWriter = csv.writer(outputFile)

    neuTB = 0
    negTB = 0
    posTB = 0

    neu = 0
    neg = 0
    pos = 0

    neuFollowers = 0
    negFollowers = 0
    posFollowers = 0

    neuRetweets = 0
    negRetweets = 0
    posRetweets = 0

    for tweet in allTweets:

        my_dict = {"text":[],"followers_count":[],"retweet_count":[]};
        my_dict["text"].append(tweet.text.encode('utf-8'))
        my_dict["followers_count"].append(tweet.user.followers_count)
        my_dict["retweet_count"].append(tweet.retweet_count)
        arrayTweets.append(my_dict)

        blob = TextBlob(tweet.text)
        polarity = blob.sentiment.polarity
        print(polarity)

        if (polarity == 0):
            neuTB += 1
        elif (polarity <= 1 and polarity > 0):
            posTB += 1
        elif (polarity < 0 and polarity >= -1):
            negTB += 1

        analyser = SentimentIntensityAnalyzer()
        score = analyser.polarity_scores(tweet.text)
        # print(score['compound'])

        if (score['compound'] == 0):
            neu += 1
            neuFollowers += tweet.user.followers_count
            neuRetweets += tweet.retweet_count
        elif (score['compound'] <= 1 and score['compound'] > 0):
            pos += 1
            posFollowers += tweet.user.followers_count
            posRetweets += tweet.retweet_count
        elif (score['compound'] < 0 and score['compound'] >= -1):
            neg += 1
            negFollowers += tweet.user.followers_count
            negRetweets += tweet.retweet_count

    fileWriter.writerow(arrayTweets)
    outputFile.close()

    return render_template('textblobVader.html', neu=neu, pos=pos, neg=neg, tweetCount=tweetCount, posFollowers=posFollowers, neuFollowers=neuFollowers, negFollowers=negFollowers, negRetweets=negRetweets, posRetweets=posRetweets, neuRetweets=neuRetweets, neuTB=neuTB, posTB=posTB, negTB=negTB)


# ****************** single Topic live ******************

temp = [['Analysis', 'positive', 'neutral', 'negative'],
            ['Polarity', '0', '0', '0']]

@app.route('/SingleTopicTopic')
def SingleTopicData():
    with open('static/CSV/sample.json', 'w') as outfile:
        json.dump(temp, outfile)

    return render_template('singleTopicLive.html')


neu = []
neg = []
pos = []


class listener(StreamListener):
    # neu = []
    # neg = []
    # pos = []

    neuFollowers = []
    negFollowers = []
    posFollowers = []

    neuRetweets = []
    negRetweets = []
    posRetweets = []

    def on_status(self, data):

        self.dynamicChart(data)
        sendData();

        return True

    @app.route('/SingleTopicTopic')
    def dynamicChart(self, data, neu=neu, neuFollowers=neuFollowers, neuRetweets=neuRetweets, pos=pos,
                     posFollowers=posFollowers, posRetweets=posRetweets, neg=neg, negFollowers=negFollowers,
                     negRetweets=negRetweets):

        analyser = SentimentIntensityAnalyzer()
        score = analyser.polarity_scores(data.text)

        firstSearch = request.form.get('firstQuery')
        secondSearch = request.form.get('secondQuery')

        text = data.text.lower()

        if (not data.retweeted) and ('RT @' not in data.text):
            if firstSearch != None and secondSearch != None:
                if firstSearch in text:
                    print('*****' + firstSearch + '*****')
                    DualTopicAnalysis(data, firstSearch)
                elif secondSearch in text:
                    print('*****' + secondSearch + '*****')
                    DualTopicAnalysis(data, secondSearch)
        else:
            if (score['compound'] == 0):
                neu.append(1)
                neuFollowers.append(data.user.followers_count)
                neuRetweets.append(data.retweet_count)
            elif (score['compound'] <= 1 and score['compound'] > 0):
                pos.append(1)
                posFollowers.append(data.user.followers_count)
                posRetweets.append(data.retweet_count)
            elif (score['compound'] < 0 and score['compound'] >= -1):
                neg.append(1)
                negFollowers.append(data.user.followers_count)
                negRetweets.append(data.retweet_count)

            # print("positive: " + str(sum(pos)) + " neutral: " + str(sum(neu)) + " negative: " + str(sum(neg)))
            # print("positive Followers: " + str(sum(posFollowers)) + " neutral Followers: " + str(
            #     sum(neuFollowers)) + " negative Followers: " + str(sum(negFollowers)) + " negative Retweets: " + str(
            #     sum(negRetweets)) + " positive Retweets: " + str(sum(posRetweets)) + " neutral Retweets: " + str(
            #     sum(neuRetweets)))
            # print("====================")

            data = [['Analysis', 'positive', 'neutral', 'negative'],
                    ['Polarity', str(sum(pos)), str(sum(neu)), str(sum(neg))]]

            with open("static/CSV/sample.json", "w") as outfile:
                json.dump(data, outfile)

    def on_error(self, status):
        print(status)


twitterStream = Stream(auth, listener())


@app.route('/sendData', methods=['GET', 'POST'])
def sendData():
    file = open("static/CSV/sample.json")
    data = json.load(file)
    file.close()

    response = make_response(json.dumps(data))
    response.content_type = 'application/json'
    return "Analysis,Positive, Neutral, Negative \n "+ data[1][0] +","+ data[1][1] +","+ data[1][2] +","+ data[1][3]


@app.route('/startSingleLiveStream', methods=['GET', 'POST'])
def startStreaming():
    query = request.form['query']
    if request.method == 'POST':
        if request.form['submit_button'] == 'Start Stream':
            clearArrays()
            twitterStream.filter(track=[query])
        elif request.form['submit_button'] == 'Stop Stream':
            twitterStream.disconnect()
        else:
            return render_template('home.html')
    elif request.method == 'GET':
        print("No Post Back Call")
    return '', 204


# ****************** dual Topic live ******************
@app.route('/DualTopicLive')
def DualTopicData():
    return render_template('dualTopicLive.html')


@app.route('/startDualLiveStream', methods=['GET', 'POST'])
def startDualStreaming():
    firstQuery = request.form['firstQuery']
    secondQuery = request.form['secondQuery']
    if request.method == 'POST':
        if request.form['submit_button_dual'] == 'Start Stream':
            clearArrays()
            twitterStream.filter(track=[firstQuery, secondQuery])
        elif request.form['submit_button_dual'] == 'Stop Stream':
            twitterStream.disconnect()
        else:
            return render_template('home.html')
    elif request.method == 'GET':
        print("No Post Back Call")

    return '', 204

DTneuFQ = []
DTneuSQ = []
DTnegFQ = []
DTnegSQ = []
DTposFQ = []
DTposSQ = []

def clearArrays():
    neu.clear()
    pos.clear()
    neg.clear()
    DTneuFQ.clear()
    DTneuSQ.clear()
    DTnegFQ.clear()
    DTnegSQ.clear()
    DTposFQ.clear()
    DTposSQ.clear()


def DualTopicAnalysis(data, query):


    print(data.text)

    analyser = SentimentIntensityAnalyzer()
    score = analyser.polarity_scores(data.text)

    firstSearch = request.form.get('firstQuery')
    secondSearch = request.form.get('secondQuery')

    if query is firstSearch:
        print("first 11111111111111111111")
        if (score['compound'] == 0):
            DTneuFQ.append(1)
        elif (score['compound'] <= 1 and score['compound'] > 0):
            DTposFQ.append(1)
        elif (score['compound'] < 0 and score['compound'] >= -1):
            DTnegFQ.append(1)

        data = [['Analysis', 'positive', 'neutral', 'negative'],
                ['Polarity', str(sum(DTposFQ)), str(sum(DTneuFQ)), str(sum(DTnegFQ))]]

        with open("static/CSV/dualFirstQuery.json", "w") as outfile:
            json.dump(data, outfile)

    elif query is secondSearch:
        print("first 22222222222222222222222")
        if (score['compound'] == 0):
            DTneuSQ.append(1)
        elif (score['compound'] <= 1 and score['compound'] > 0):
            DTposSQ.append(1)
        elif (score['compound'] < 0 and score['compound'] >= -1):
            DTnegSQ.append(1)

        data = [['Analysis', 'positive', 'neutral', 'negative'],
                ['Polarity', str(sum(DTposSQ)), str(sum(DTneuSQ)), str(sum(DTnegSQ))]]

        with open("static/CSV/dualSecondQuery.json", "w") as outfile:
            json.dump(data, outfile)


@app.route('/FQsendData', methods=['GET', 'POST'])
def FQsendData():
    file = open("static/CSV/dualFirstQuery.json")
    data = json.load(file)
    file.close()

    response = make_response(json.dumps(data))
    response.content_type = 'application/json'
    return "Analysis,Positive, Neutral, Negative \n "+ data[1][0] +","+ data[1][1] +","+ data[1][2] +","+ data[1][3]


@app.route('/SQsendData', methods=['GET', 'POST'])
def SQsendData():
    file = open("static/CSV/dualSecondQuery.json")
    data = json.load(file)
    file.close()

    response = make_response(json.dumps(data))
    response.content_type = 'application/json'
    return "Analysis,Positive, Neutral, Negative \n "+ data[1][0] +","+ data[1][1] +","+ data[1][2] +","+ data[1][3]




#================================


if __name__ == '__main__':
    app.run()





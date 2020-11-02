import os
import pandas as pd
import json
import tweepy as tp
import csv
import re
from flask import Flask, render_template, request
from twitter_auth import API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import ast

auth = tp.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

api = tp.API(auth)

app = Flask(__name__)

allTweets = []
arrayTweets = []

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/textblobVader')
def staticData():
    if os.path.isfile('static/CSV/output.csv') is False:
        return getStaticTweets()
    else:
        if os.path.getsize('static/CSV/output.csv') == 0:
            return getStaticTweets()
        else:
            neu = 0
            neg = 0
            pos = 0

            neuFollowers = 0
            negFollowers = 0
            posFollowers = 0

            neuRetweets = 0
            negRetweets = 0
            posRetweets = 0

            tweetCount = 0

            df = pd.read_csv('static/CSV/output.csv', header=None)
            for row in df.iterrows():
                ent = row[1]

                for i in range(len(ent)):

                    tweet = ent.values[i]
                    tweet = ast.literal_eval(tweet)

                    tweetText = list(tweet.values())[0]
                    tweetText = ', '.join(map(str, tweetText))
                    #print(tweetText)

                    tweetFollowersCount = list(tweet.values())[1]
                    tweetFollowersCount = ', '.join(map(str, tweetFollowersCount))
                    #print(tweetFollowersCount)

                    tweetRetweetCount = list(tweet.values())[2]
                    tweetRetweetCount = ', '.join(map(str, tweetRetweetCount))
                    #print(tweetRetweetCount)

                    analyser = SentimentIntensityAnalyzer()
                    score = analyser.polarity_scores(tweetText)
                    # print(score['compound'])

                    tweetCount += 1

                    if (score['compound'] == 0):
                        neu += 1
                        neuFollowers += int(tweetFollowersCount)
                        neuRetweets += int(tweetRetweetCount)
                    elif (score['compound'] <= 1 and score['compound'] > 0):
                        pos += 1
                        posFollowers += int(tweetFollowersCount)
                        posRetweets += int(tweetRetweetCount)
                    elif (score['compound'] < 0 and score['compound'] >= -1):
                        neg += 1
                        negFollowers += int(tweetFollowersCount)
                        negRetweets += int(tweetRetweetCount)

            print("positive Followers: " + str(posFollowers) + " neutral Followers: " + str(neuFollowers) + " negative Followers: " + str(negFollowers) + " negative Retweets: " + str(negRetweets) + " positive Retweets: " + str(posRetweets) + " neutral Retweets: " + str(neuRetweets))

            return render_template('textblobVader.html', neu=neu, pos=pos, neg=neg, tweetCount=tweetCount, posFollowers=posFollowers, neuFollowers=neuFollowers, negFollowers=negFollowers, negRetweets=negRetweets, posRetweets=posRetweets, neuRetweets=neuRetweets)


def getStaticTweets():
    tweetCount = 40
    allTweets = tp.Cursor(api.search, q="trump", lang="en").items(tweetCount)

    outputFile = open('static/CSV/output.csv', 'a')
    fileWriter = csv.writer(outputFile)

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
        # print(my_dict["text"])
        arrayTweets.append(my_dict)

        # blob = TextBlob(tweet.text)
        # polarity = blob.sentiment.polarity
        # print(polarity)

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

    #print("positive: " + str(pos) + " neutral: " + str(neu) + " negative: " + str(neg))
    # print("positive Followers: " + str(posFollowers) + " neutral Followers: " + str(neuFollowers) + " negative Followers: " + str(negFollowers))

    return render_template('textblobVader.html', neu=neu, pos=pos, neg=neg, tweetCount=tweetCount, posFollowers=posFollowers, neuFollowers=neuFollowers, negFollowers=negFollowers, negRetweets=negRetweets, posRetweets=posRetweets, neuRetweets=neuRetweets)


if __name__ == '__main__':
    app.run()

#======================================
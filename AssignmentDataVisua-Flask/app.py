import tweepy as tp
import csv
import re
from flask import Flask, render_template, request
from twitter_auth import API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
from textblob import TextBlob

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
def textblobVader():
    allTweets = tp.Cursor(api.search, q="trump", lang="en").items(10)

    outputFile = open('static/output.csv', 'a')
    fileWriter = csv.writer(outputFile)

    neu = 0
    neg = 0
    pos = 0

    for tweet in allTweets:
        ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t]) | (\w +:\ / \ / \S +)", " ", str(tweet)).split())
        arrayTweets.append(tweet.text.encode('utf-8'))
        blob = TextBlob(tweet.text)
        polarity = blob.sentiment.polarity
        #print(polarity)

        if (polarity == 0):
            neu += 1
        elif (polarity <= 1 and polarity > 0):
            pos += 1
        elif (polarity < 0 and polarity >= -1):
            neg += 1

    fileWriter.writerow(arrayTweets)
    outputFile.close()

    #print("positive: " + str(pos) + " neutral: " + str(neu) + " negative: " + str(neg))

    return render_template('textblobVader.html', neu=neu, pos=pos, neg=neg)


if __name__ == '__main__':
    app.run()


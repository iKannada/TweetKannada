# -*- coding: utf-8 -*-
import tweepy
import json
import operator
import MySQLdb
import re
from authorization import authorize_user

blacklisted_words = [u"RT", u"via", u"https://…", u"http://…", u"https://t…", u"Read"]


# Using twitter search instead of streaming since KN is not yet supported
def is_blacklisted(word):
    if word.startswith('@'):  # Twitter Username
        return True
    if word.startswith('&'):
        return True
    if word in blacklisted_words:  # Look to handle it better.
        return True
    if len(word) < 3:  # Mostly conjunction words
        return True
    return False


def update_word_counts(text):
    for word in text.split():
        if is_blacklisted(word):
            continue
        word_count_map[word] = word_count_map.get(word, 0) + 1


def remove_escape_sequence(word):
    return word.replace('\_', '_')


username = raw_input("Enter the username to authenticate:")
with open('user_configs.txt', 'r') as input_file:
    user_configs = json.load(input_file)

with open('configs.txt', 'r') as input_file:
    configs = json.load(input_file)

word_count_map = {}

app_consumer_key = configs['app_consumer_key']
app_consumer_secret = configs['app_consumer_secret']

if username in user_configs:
    user_config = user_configs[username]
    access_token = user_config["access_token"]
    access_token_secret = user_config["access_token_secret"]
    auth = tweepy.OAuthHandler(app_consumer_key, app_consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
else:
    auth = authorize_user(app_consumer_key, app_consumer_secret)
    user_configs[auth.get_username()] = {"access_token": auth.access_token,
                                         "access_token_secret": auth.access_token_secret}

twitter_api = tweepy.API(auth)
NO_OF_SEARCH_RESULTS = 100
latest_tweet_id = configs.get('latest_tweet_id')
search_results = twitter_api.search(q="lang:kn", since_id=latest_tweet_id, count=NO_OF_SEARCH_RESULTS)

if search_results:
    latest_tweet_id = search_results[0].id
    configs['latest_tweet_id'] = latest_tweet_id

with open('user_configs.txt', 'w+') as outfile:
    json.dump(user_configs, outfile)

with open('configs.txt', 'w+') as outfile:
    json.dump(configs, outfile)

database_name = "twitter_trends"
db_username = "root"
db_password = "root"
db_host = "localhost"
db = MySQLdb.connect(db_host, db_username, db_password, database_name)

# prepare a cursor object using cursor() method
db.set_character_set('utf8')
cursor = db.cursor()
cursor.execute('SET NAMES utf8;')
cursor.execute('SET CHARACTER SET utf8;')
cursor.execute('SET character_set_connection=utf8;')

# re.escape do I need to use if for tweet text?
for tweet in search_results:
    sql = u"""INSERT INTO tweets (twitter_text, created_date) VALUES('%s','%s');""" % (
        re.escape(unicode(tweet.text)), unicode(tweet.created_at))
    cursor.execute(sql)

# Call DB and get all tweets for last two hours.
cursor.execute("""select * from tweets where created_date > DATE_SUB(UTC_TIMESTAMP(),INTERVAL 2 HOUR);""")
latest_tweets = cursor.fetchall()

for tweet in latest_tweets:
    update_word_counts(tweet[1].decode('utf-8'))

top_trends = sorted(word_count_map.items(), key=operator.itemgetter(1), reverse=True)

db.commit()
# disconnect from server
db.close()
tweet = u"ಇತ್ತೀಚಿನ ಕನ್ನಡ ಟ್ವೀಟಲ್ಲಿ ಹೆಚ್ಚು ಬಳಸಿದ ಪದಗಳು: "

selected_trends = []
trends_text = u", ".join(selected_trends)
while len(trends_text) < 140 - len(tweet):
    selected_trends.append(top_trends.pop(0)[0])
    trends_text = u", ".join(selected_trends)

tweet += trends_text
print tweet
twitter_api.update_status(status=tweet)

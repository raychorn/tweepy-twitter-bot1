# Tripping Tweepy Twitter Bot.

## Table of Contents

- [Tripping Tweepy Twitter Bot.](#tripping-tweepy-twitter-bot)
  - [Table of Contents](#table-of-contents)
  - [About](#about)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
      - [docker .env](#docker-env)
      - [.env](#env)
    - [Installing](#installing)
  - [Usage <a name = "usage"></a>](#usage-)
  - [Poor Man's Crontab Monitor](#poor-mans-crontab-monitor)

## About

Tweets are schedule and rotated dynamically based on a number of seconds.

## Getting Started

Install and use it.

### Prerequisites

Python 3.x, Python 3.9.1 was used.

#### docker .env

```
# MongoDB
MONGO_URL=mongodb://mongodb:27017
MONGO_INITDB_ROOT_USERNAME=
MONGO_INITDB_ROOT_PASSWORD=
MONGO_INITDB_DATABASE=
MONGO_REPLICA_SET_NAME=rs0
MONGO_AUTH_MECHANISM=SCRAM-SHA-256

SECRETS=
PYTHONPATH=.:/workspaces/microservices-framework/microservices-framework/python_lib3/vyperlogix38.zip:/workspaces/microservices-framework/microservices-framework/.venv387/lib/python3.8/site-packages
DJANGO_LOG_LEVEL=INFO
```

#### .env 

```
__LITERALS__=MONGO_INITDB_ROOT_PASSWORD # item|item
__ESCAPED__=MONGO_INITDB_ROOT_USERNAME|MONGO_INITDB_ROOT_PASSWORD # item|item

__domain__=0.0.0.0:9000
__uuid__=vyperapi-uuid-goes-here

access_token=
access_token_secret=
consumer_key=
consumer_secret=

bityly_username=
bitly_access_token=

MONGO_INITDB_DATABASE=admin
MONGO_HOST=
MONGO_PORT=27017
MONGO_URI=mongodb://$MONGO_HOST:$MONGO_PORT/?connectTimeoutMS=300000
MONGO_INITDB_ROOT_USERNAME=
MONGO_INITDB_ROOT_PASSWORD=
MONGO_AUTH_MECHANISM=SCRAM-SHA-256

IGNORING=MONGO_CLUSTER # item|item
MONGO_CLUSTER=mongodb+srv://root:$MONGO_INITDB_ROOT_PASSWORD@cluster0.as9re.mongodb.net/$MONGO_INITDB_DATABASE?retryWrites=true&w=majority
MONGO_CLUSTER_AUTH_MECHANISM=

OPTIONS=use_cluster

mongo_db_name=WORD-CLOUD
mongo_articles_col_name=articles
mongo_article_text_col_name=articles_text
mongo_words_col_name=words
mongo_cloud_col_name=word-cloud
mongo_hashtags_col_name=hashtags

minimum_url_length=40

plugins=/home/raychorn/projects/python-projects/tweepy-twitter-bot1/plugins

minimum_word_cloud_count=1
minimum_hashtags_length=6
hashtags_criteria=is_uppercase

hashtags_followers_pace=15

twitter_rate_limit=0.30

twitter_follow_followers=0 # 1 for production
```

### Installing

1. git clone blah-blah-blah
2. Modify the docker stuff for your needs.
3. ./docker-up.sh
4. Make it work.

## Usage <a name = "usage"></a>

Run the code.  Supply your own database.  I used Mongo.

## Poor Man's Crontab Monitor

```
crontab -e
0 0 * * * /home/ubuntu/tweepy-twitter-bot1/scripts/cron-job.sh >> /home/ubuntu/tweepy-twitter-bot1/scripts/cron-job.log 2>&1
0 1 * * * /home/ubuntu/tweepy-twitter-bot1/scripts/truncate-cron-log.sh
```

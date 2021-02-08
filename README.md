# Tripping Tweepy Twitter Bot.

## Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)

## About <a name = "about"></a>

Tweets are schedule and rotated dynamically based on a number of seconds.

## Getting Started <a name = "getting_started"></a>

Install and use it.

### Prerequisites

Python 3.x, Python 3.9.1 was used.

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

twitter_rate_limit=0.3
```

### Installing

git clone blah-blah-blah

## Usage <a name = "usage"></a>

Run the code.  Supply your own database.  I used Mongo.

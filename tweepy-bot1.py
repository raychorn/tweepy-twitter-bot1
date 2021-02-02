import os
import sys
import time
import math
import random
import mujson as json
import tweepy
import pprint
import traceback

from datetime import datetime

import logging
logger = logging.getLogger(__name__)

log_filename = '{}{}{}.log'.format(os.path.dirname(__file__), os.sep, os.path.splitext(os.path.basename(__file__))[0])

if (os.path.exists(log_filename)):
    os.remove(log_filename)

log_format = ('[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s')
logging.basicConfig(
    level=logging.DEBUG,
    format=log_format,
    filename=(log_filename),
)


pylib = '/home/raychorn/projects/python-projects/private_vyperlogix_lib3/zips/vyperlogix39.zip'
if (not any([f == pylib for f in sys.path])):
    print('Adding {}'.format(pylib))
    sys.path.insert(0, pylib)
    
from vyperlogix.misc import _utils
from vyperlogix.env import environ
from vyperlogix.bitly import shorten

from vyperlogix.mongo import vyperapi
from vyperlogix.decorators import __with
from bson.objectid import ObjectId
from vyperlogix.iterators.dict import dictutils

__env__ = {}
def get_environ_keys(*args, **kwargs):
    k = kwargs.get('key')
    v = kwargs.get('value')
    assert (k is not None) and (v is not None), 'Problem with kwargs -> {}, k={}, v={}'.format(kwargs,k,v)
    environ = kwargs.get('environ', {})
    __env__[k] = v
    if (environ.get(k) == None):
        environ[k] = v
    print('\t{} -> {}'.format(k, v))
    return True

env_path = '/home/raychorn/projects/python-projects/tweepy-twitter-bot1/.env'

environ.load_env(env_path=env_path, environ=os.environ, cwd=env_path, verbose=True, ignoring_re='.git|.venv|__pycache__', callback=lambda *args, **kwargs:get_environ_keys(args, **kwargs))


access_token = os.environ.get('access_token')
access_token_secret = os.environ.get('access_token_secret')
consumer_key = os.environ.get('consumer_key')
consumer_secret = os.environ.get('consumer_secret')

assert access_token and len(access_token), 'Missing access_token.'
assert access_token_secret and len(access_token_secret), 'Missing access_token_secret.'
assert consumer_key and len(consumer_key), 'Missing consumer_key.'
assert consumer_secret and len(consumer_secret), 'Missing consumer_secret.'

__domain__ = os.environ.get('__domain__')
__uuid__ = os.environ.get('__uuid__')

assert __domain__ and len(__domain__), 'Missing __domain__.'
assert __uuid__ and len(__uuid__), 'Missing __uuid__.'

mongo_db_name = os.environ.get('mongo_db_name')
mongo_articles_col_name = os.environ.get('mongo_articles_col_name')
mongo_article_text_col_name = os.environ.get('mongo_article_text_col_name')
mongo_words_col_name = os.environ.get('mongo_words_col_name')
mongo_cloud_col_name = os.environ.get('mongo_cloud_col_name')

assert mongo_db_name and len(mongo_db_name), 'Missing mongo_db_name.'
assert mongo_articles_col_name and len(mongo_articles_col_name), 'Missing mongo_articles_col_name.'
assert mongo_article_text_col_name and len(mongo_article_text_col_name), 'Missing mongo_article_text_col_name.'
assert mongo_words_col_name and len(mongo_words_col_name), 'Missing mongo_words_col_name.'
assert mongo_cloud_col_name and len(mongo_cloud_col_name), 'Missing mongo_cloud_col_name.'


def __get_articles(_id=None, criteria=None, callback=None):
    @__with.database(environ=__env__)
    def db_get_articles(db=None):
        assert vyperapi.is_not_none(db), 'There is no db context.'

        tb_name = mongo_db_name
        col_name = mongo_articles_col_name
        table = db[tb_name]
        coll = table[col_name]

        find_in_collection = lambda c,criteria=criteria:c.find() if (not criteria) else c.find(criteria)
        recs = []
        if (not _id):
            recs = [str(doc.get('_id')) for doc in find_in_collection(coll, criteria=criteria)]
        else:
            recs = coll.find_one({"_id": ObjectId(_id)})
        if (callable(callback)):
            callback(coll=coll, recs=recs, _id=_id)
        return recs
    return db_get_articles()


def __get_articles(_id=None, criteria=None, callback=None):
    @__with.database(environ=__env__)
    def db_get_articles(db=None):
        assert vyperapi.is_not_none(db), 'There is no db context.'

        tb_name = mongo_db_name
        col_name = mongo_articles_col_name
        table = db[tb_name]
        coll = table[col_name]

        find_in_collection = lambda c,criteria=criteria:c.find() if (not criteria) else c.find(criteria)
        recs = []
        if (not _id):
            recs = [str(doc.get('_id')) for doc in find_in_collection(coll, criteria=criteria)]
        else:
            recs = coll.find_one({"_id": ObjectId(_id)})
        if (callable(callback)):
            callback(coll=coll, recs=recs, _id=_id)
        return recs
    return db_get_articles()



def __store_article_data(data, update=None):
    @__with.database(environ=__env__)
    def db_store_article_data(db=None, data=None):
        assert vyperapi.is_not_none(db), 'There is no db context.'

        tb_name = mongo_db_name
        col_name = mongo_articles_col_name
        table = db[tb_name]
        coll = table[col_name]

        count = -1
        u = data.get('url')
        if (u) and (len(u) > 0):
            d = dict([tuple(t.split('=')) for t in u.split('?')[-1].split('&')])
            k = d.get('source')
            v = d.get('sk')
            if (k and v):
                data[k] = v
            doc = coll.find_one({ "url": u })
            if (doc):
                if (any([k.find('_time') > -1 for k in update.keys()])):
                    newvalue = { "$set": update }
                else:
                    data['updated_time'] = datetime.utcnow()
                    newvalue = { "$set": data }
                coll.update_one({'_id': doc.get('_id')}, newvalue)
            else:
                data['created_time'] = datetime.utcnow()
                coll.insert_one(data)

            count = coll.count_documents({})
        return count
    return db_store_article_data(data=data)



def get_hashtags_for(api, screen_name, count=200, verbose=False, hashtags_dict={}):
    tweets = api.user_timeline(screen_name=screen_name,count=count)
    for tweet in tweets:
        hashtags = tweet.entities.get('hashtags')
        for hashtag in hashtags:
            if hashtag['text'] in hashtags_dict.keys():
                hashtags_dict[hashtag['text']] += 1
            else:
                hashtags_dict[hashtag['text']] = 1

    if (verbose):
        tags = sorted(hashtags_dict, key=hashtags_dict.get, reverse=True)
        for t in tags:
            print('{} -> {}'.format(t, hashtags_dict.get(t)))
    return hashtags_dict
    
    
def get_top_trending_hashtags(api):
    data = api.trends_place(1)
    hashtags = dict([tuple([trend['name'], trend['tweet_volume']]) for trend in data[0]['trends'] if (trend['name'].startswith('#')) and (len(_utils.ascii_only(trend['name'])) == len(trend['name']))])
    return _utils.sorted_dict(hashtags, reversed=True, default=-1)
    

def get_shorter_url(url):
    bitly_access_token = os.environ.get('bitly_access_token')
    assert bitly_access_token and (len(bitly_access_token) > 0), 'Missing the bitly_access_token. Check your .env file.'

    return shorten(url, token=bitly_access_token)


def do_the_tweet(api, item, popular_hashtags=None):
    sample_tweet = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    url = item.get('url')
    assert url and (len(url) > 0), 'Problem with URL in do_the_tweet().'
    u = get_shorter_url(url) if (len(url) > int(os.environ.get('minimum_url_length', 40))) else url
    msg = 'URL: {} -> {}'.format(url, u)
    print(msg)
    logger.info(msg)
    the_tweet = '{}\n{}\n(raychorn.github.io + raychorn.medium.com)\n'.format(item.get('name'), u)
    num_chars = len(sample_tweet) - len(the_tweet)
    popular_hashtags = get_top_trending_hashtags(api) if (not popular_hashtags) else popular_hashtags
    if (num_chars > 0):
        while (1):
            if (len(popular_hashtags) > 0):
                hashtag = popular_hashtags[0]
                if (len(the_tweet) + len(hashtag) + 1) < len(sample_tweet):
                    the_tweet += ' {}'.format(hashtag)
                    del popular_hashtags[0]
                else:
                    break
            else:
                break
    print('TWEET:\n{}'.format(the_tweet))
    logger.info('BEGIN: TWEET')
    logger.info(the_tweet)
    logger.info('END!!! TWEET')
    if (1):
        api.update_status(the_tweet)


def log_traceback(ex, ex_traceback=None):
    if ex_traceback is None:
        ex_traceback = ex.__traceback__
    tb_lines = [ line.rstrip('\n') for line in
                traceback.format_exception(ex.__class__, ex, ex_traceback)]
    logger.critical(tb_lines)


if (__name__ == '__main__'):
    try:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
    except:
        msg = 'Problem connecting to the twitter?'
        print(msg)
        logger.error(msg)
        sys.exit()

    the_rotation = {}
    num_choices = 0
    while(1):
        try:
            print('\n'*10)
            ts_current_time = _utils.timeStamp(offset=0, use_iso=True)
            msg = 'Current time: {}'.format(ts_current_time)
            print(msg)
            logger.info(msg)

            tweet_period_secs = 1*60*60
            
            ts_tweeted_time = _utils.timeStamp(offset=-tweet_period_secs, use_iso=True)
            msg = 'Tweeted time:  {}'.format(ts_tweeted_time)
            print(msg)
            logger.info(msg)

            print('\n'*2)

            the_list = __get_articles()
            
            the_real_list = []
            for anId in the_list:
                item = __get_articles(_id=anId)
                if (item):
                    sz = item.get('friends_link')
                    tt = item.get('tweeted_time')
                    msg = 'id: {}, sz: {}, tt: {}'.format(anId, sz, tt)
                    print(msg)
                    logger.info(msg)
                    
                    if (tt is None):
                        the_real_list.append(anId)
                        msg = 'Added to the_real_list: {}\n'.format(anId)
                        print(msg)
                        logger.info(msg)
                        continue
                    
                    dt_target = datetime.fromisoformat(ts_tweeted_time)
                    dt_item = datetime.fromisoformat(tt)
                    delta = max(dt_target, dt_item) - min(dt_target, dt_item)
                    __is__ = delta.total_seconds() > tweet_period_secs
                    msg = 'delta: {}, dt_target: {}, dt_item: {}, delta.total_seconds(): {}, tweet_period_secs: {}, __is__: {}'.format(delta, dt_target, dt_item, delta.total_seconds(), tweet_period_secs, __is__)
                    print(msg)
                    logger.info(msg)
                    
                    if (__is__):
                        the_real_list.append(anId)
                        msg = 'Added to the_real_list: {}\n'.format(anId)
                        print(msg)
                        logger.info(msg)
                        continue
            msg = '='*30
            print(msg)
            logger.info(msg)

            msg = 'the_real_list has {} items and the_list has {} items.'.format(len(the_real_list), len(the_list))
            print(msg)
            logger.info(msg)
            
            required_velocity = math.ceil(len(the_list) / 24)
            
            the_chosen = set()
            random.seed(datetime.now())
            wait_per_choice = tweet_period_secs / int(required_velocity)
            for i in range(int(required_velocity)):
                the_choice = list(set(the_real_list) - the_chosen)[random.randint(0, len(list(set(the_real_list) - the_chosen)))]
                print('the_choice: {}'.format(the_choice))
                
                the_chosen.add(the_choice)

                item = __get_articles(_id=the_choice)
                assert item, 'Did not retrieve an item for {}.'.format(the_choice)
                if (item):
                    do_the_tweet(api, item)
                    the_update = { 'tweeted_time': ts_current_time}
                    msg = 'Updating: id: {}, {}'.format(the_choice, the_update)
                    print(msg)
                    logger.info(msg)
                    resp = __store_article_data(item, update=the_update)
                    assert isinstance(resp, int), 'Problem with the response? Expected int value but got {}'.format(resp)
                    print('Update was done.')
                    
                    b = the_rotation.get(the_choice, [])
                    b.append(ts_current_time)
                    the_rotation[the_choice] = b
                    num_choices += 1
                    
                    if (num_choices % len(the_list)) == 0:
                        msg = 'BEGIN: the_rotation'
                        print(msg)
                        logger.info(msg)
                        
                        for k,values in the_rotation.items():
                            msg = '{}'.format(k)
                            print(msg)
                            logger.info(msg)
                            for v in values:
                                msg = '\t{}'.format(v)
                                print(msg)
                                logger.info(msg)
                        msg = 'END!!! the_rotation'
                        print(msg)
                        logger.info(msg)
                    print('\n'*2)
                msg = 'Sleeping for {} mins for choice. (Press any key to exit.)'.format(int(wait_per_choice / 60))
                print(msg)
                logger.info(msg)
                time.sleep(wait_per_choice)
            msg = 'Sleeping for {} mins. (Press any key to exit.)'.format(int(tweet_period_secs / 60))
            print(msg)
            logger.info(msg)
            time.sleep(tweet_period_secs)
        except KeyboardInterrupt:
            msg = 'KeyboardInterrupt.'
            print(msg)
            logger.info(msg)
            break
        except Exception as ex:
            extype, ex, tb = sys.exc_info()
            formatted = traceback.format_exception_only(extype, ex)[-1]
            for l in traceback.format_exception(extype, ex, tb):
                print(l.rstrip())
                logger.error(l.rstrip())
            break        

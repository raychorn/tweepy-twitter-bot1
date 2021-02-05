import os
import sys
import time
import math
import random
import mujson as json
import tweepy
import pprint
import logging
from logging.handlers import RotatingFileHandler
import traceback

from datetime import datetime

is_really_something = lambda s,t:s and t(s)
something_greater_than_zero = lambda s:(s > 0)

default_timestamp = lambda t:t.isoformat().replace(':', '').replace('-','').split('.')[0]

is_uppercase = lambda ch:''.join([c for c in str(ch) if c.isupper()])


def get_stream_handler(streamformat="%(asctime)s:%(levelname)s:%(message)s"):
    stream = logging.StreamHandler()
    stream.setLevel(logging.INFO)
    stream.setFormatter(logging.Formatter(streamformat))
    return stream

    
def setup_rotating_file_handler(logname, logfile, max_bytes, backup_count):
    assert is_really_something(backup_count, something_greater_than_zero), 'Missing backup_count?'
    assert is_really_something(max_bytes, something_greater_than_zero), 'Missing max_bytes?'
    ch = RotatingFileHandler(logfile, 'a', max_bytes, backup_count)
    l = logging.getLogger(logname)
    l.addHandler(ch)
    return l


base_filename = os.path.splitext(os.path.basename(__file__))[0]

log_filename = '{}{}{}{}{}_{}.log'.format('logs', os.sep, base_filename, os.sep, base_filename, default_timestamp(datetime.utcnow()))

if not os.path.exists(os.path.dirname(log_filename)):
    os.makedirs(os.path.dirname(log_filename))

if (os.path.exists(log_filename)):
    os.remove(log_filename)

log_format = ('[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s')
logging.basicConfig(
    level=logging.DEBUG,
    format=log_format,
    filename=(log_filename),
)

logger = setup_rotating_file_handler(base_filename, log_filename, (1024*1024*1024), 10)
logger.addHandler(get_stream_handler())


twitter_verse = 'twitter_verse'
get_api = 'get_api'
do_the_tweet = 'do_the_tweet'


articles_list = 'articles_list'
get_the_real_list = 'get_the_real_list'
update_the_article = 'update_the_article'
get_articles = 'get_articles'
get_a_choice = 'get_a_choice'
get_more_followers = 'get_more_followers'


word_cloud = 'word_cloud'
get_final_word_cloud = 'get_final_word_cloud'
store_one_hashtag = 'store_one_hashtag'


pylib = '/home/raychorn/projects/python-projects/private_vyperlogix_lib3'
if (not any([f == pylib for f in sys.path])):
    print('Adding {}'.format(pylib))
    sys.path.insert(0, pylib)
    
from vyperlogix.misc import _utils
from vyperlogix.env import environ
from vyperlogix.plugins import handler as plugins_handler

__env__ = {}
env_literals = ['MONGO_INITDB_ROOT_PASSWORD']
def get_environ_keys(*args, **kwargs):
    from expandvars import expandvars
    
    k = kwargs.get('key')
    v = kwargs.get('value')
    assert (k is not None) and (v is not None), 'Problem with kwargs -> {}, k={}, v={}'.format(kwargs,k,v)
    __logger__ = kwargs.get('logger')
    v = expandvars(v) if (k not in env_literals) else v
    environ = kwargs.get('environ', {})
    __env__[k] = str(v)
    environ[k] = str(v)
    if (__logger__):
        __logger__.info('\t{} -> {}'.format(k, environ.get(k)))
    return True

env_path = '/home/raychorn/projects/python-projects/tweepy-twitter-bot1/.env'

environ.load_env(env_path=env_path, environ=os.environ, cwd=env_path, verbose=True, logger=logger, ignoring_re='.git|.venv|__pycache__', callback=lambda *args, **kwargs:get_environ_keys(args, **kwargs))

is_really_a_string = lambda s:s and len(s)

access_token = os.environ.get('access_token', __env__.get('access_token'))
access_token_secret = os.environ.get('access_token_secret', __env__.get('access_token_secret'))
consumer_key = os.environ.get('consumer_key', __env__.get('consumer_key'))
consumer_secret = os.environ.get('consumer_secret', __env__.get('consumer_secret'))

assert is_really_a_string(access_token), 'Missing access_token.'
assert is_really_a_string(access_token_secret), 'Missing access_token_secret.'
assert is_really_a_string(consumer_key), 'Missing consumer_key.'
assert is_really_a_string(consumer_secret), 'Missing consumer_secret.'

__domain__ = os.environ.get('__domain__', __env__.get('__domain__'))
__uuid__ = os.environ.get('__uuid__', __env__.get('__uuid__'))

assert is_really_a_string(__domain__), 'Missing __domain__.'
assert is_really_a_string(__uuid__), 'Missing __uuid__.'

mongo_db_name = os.environ.get('mongo_db_name', __env__.get('mongo_db_name'))
mongo_articles_col_name = os.environ.get('mongo_articles_col_name', __env__.get('mongo_articles_col_name'))
mongo_article_text_col_name = os.environ.get('mongo_article_text_col_name', __env__.get('mongo_article_text_col_name'))
mongo_words_col_name = os.environ.get('mongo_words_col_name', __env__.get('mongo_words_col_name'))
mongo_cloud_col_name = os.environ.get('mongo_cloud_col_name', __env__.get('mongo_cloud_col_name'))

assert is_really_a_string(mongo_db_name), 'Missing mongo_db_name.'
assert is_really_a_string(mongo_articles_col_name), 'Missing mongo_articles_col_name.'
assert is_really_a_string(mongo_article_text_col_name), 'Missing mongo_article_text_col_name.'
assert is_really_a_string(mongo_words_col_name), 'Missing mongo_words_col_name.'
assert is_really_a_string(mongo_cloud_col_name), 'Missing mongo_cloud_col_name.'


plugins = __env__.get('plugins')
assert is_really_a_string(plugins) and os.path.exists(plugins), 'Missing plugins.'


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
    
def log_traceback(ex, ex_traceback=None):
    if ex_traceback is None:
        ex_traceback = ex.__traceback__
    tb_lines = [ line.rstrip('\n') for line in
                traceback.format_exception(ex.__class__, ex, ex_traceback)]
    logger.critical(tb_lines)


def get_top_trending_hashtags(api):
    data = api.trends_place(1)
    hashtags = dict([tuple([trend['name'], trend['tweet_volume']]) for trend in data[0]['trends'] if (trend['name'].startswith('#')) and (len(_utils.ascii_only(trend['name'])) == len(trend['name']))])
    return _utils.sorted_dict(hashtags, reversed=True, default=-1)
    

if (__name__ == '__main__'):
    plugins_manager = plugins_handler.PluginManager(plugins, debug=True)
    service_runner = plugins_manager.get_runner()
    
    api = service_runner.exec(twitter_verse, get_api, **plugins_handler.get_kwargs(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_token, access_token_secret=access_token_secret, logger=logger))
    
    if (1):
        hashtags = []
        if (0):
            criteria = os.environ.get('hashtags_criteria')
            if (criteria.find('is_uppercase') > -1):
                criteria = is_uppercase
            threshold = int(os.environ.get('minimum_word_cloud_count', 1))
            min_hashtag_length = int(os.environ.get('minimum_hashtags_length', 1))
            words = service_runner.exec(word_cloud, get_final_word_cloud, **plugins_handler.get_kwargs(environ=os.environ, callback=None, logger=logger))
            for k,v in words.get('word-cloud', {}).items():
                if ( (len(k) > min_hashtag_length) and (v > threshold) ) or (criteria(k)):
                    hashtags.append(k)
        service_runner.exec(twitter_verse, get_more_followers, **plugins_handler.get_kwargs(api=api, environ=__env__, service_runner=service_runner, hashtags=hashtags, silent=False, runtime=0, logger=logger))

    if (0):
        h = get_top_trending_hashtags(api)
        print(h)

    while(1):
        try:
            print('\n'*10)
            ts_current_time = _utils.timeStamp(offset=0, use_iso=True)
            msg = 'Current time: {}'.format(ts_current_time)
            logger.info(msg)

            tweet_period_secs = 1*60*60
            
            ts_tweeted_time = _utils.timeStamp(offset=-tweet_period_secs, use_iso=True)
            msg = 'Tweeted time:  {}'.format(ts_tweeted_time)
            logger.info(msg)
            
            if (0):
                today = _utils.today_utctime()
                secs_until_tomorrow_morning = ((24 - today.hour) * (60*60)) + ((59 - today.minute) * 60)
                tomorrow_morning = _utils.timeStamp(offset=secs_until_tomorrow_morning, use_iso=True)
                dt_tomorrow_morning = datetime.fromisoformat(tomorrow_morning)
                delta = max(dt_tomorrow_morning, today) - min(dt_tomorrow_morning, today)
            secs_until_tomorrow_morning = 24*60*60 #  max(delta.total_seconds(), secs_until_tomorrow_morning)

            print('\n'*2)

            the_list = service_runner.exec(articles_list, get_articles, **plugins_handler.get_kwargs(_id=None, environ=__env__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name))
            
            wait_per_choice = secs_until_tomorrow_morning / len(the_list)
            msg = 'wait_per_choice: {}'.format(wait_per_choice)
            logger.info(msg)
            
            the_real_list = service_runner.exec(articles_list, get_the_real_list, **plugins_handler.get_kwargs(the_list=the_list, logger=logger, ts_tweeted_time=ts_tweeted_time, tweet_period_secs=tweet_period_secs, environ=__env__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name))

            msg = '='*30
            logger.info(msg)

            msg = 'the_real_list has {} items and the_list has {} items.'.format(len(the_real_list), len(the_list))
            logger.info(msg)
            
            required_velocity = len(the_real_list)
            msg = 'required_velocity: {}'.format(required_velocity)
            logger.info(msg)
            
            the_chosen = []
            random.seed(int(time.time()))
            total_wait_for_choices = 0
            for i in range(int(required_velocity)):
                the_choice = service_runner.exec(articles_list, get_a_choice, **plugins_handler.get_kwargs(the_list=the_real_list, the_chosen=the_chosen, logger=logger))
                assert the_choice, 'Nothing in the list?  Please check.'
                msg = 'the_choice: {}'.format(the_choice)
                logger.info(msg)
                
                if (the_choice):
                
                    the_chosen.append(the_choice)
                    msg = 'the_chosen has {} items.'.format(len(the_chosen))
                    logger.info(msg)

                    item = service_runner.exec(articles_list, get_articles, **plugins_handler.get_kwargs(_id=the_choice, environ=__env__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name))
                    assert item, 'Did not retrieve an item for {}.'.format(the_choice)
                    if (item):
                        service_runner.exec(twitter_verse, do_the_tweet, **plugins_handler.get_kwargs(api=api, item=item, logger=logger))

                        the_rotation = service_runner.exec(articles_list, update_the_article, **plugins_handler.get_kwargs(the_choice=the_choice, environ=__env__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, logger=logger, item=item, ts_current_time=ts_current_time))
                        
                        msg = 'BEGIN: the_rotation'
                        logger.info(msg)
                        
                        for v in the_rotation:
                            msg = '\t{}'.format(v)
                            logger.info(msg)
                        msg = 'END!!! the_rotation'
                        logger.info(msg)
                        print('\n'*2)
                    msg = 'Sleeping for {} mins for choice. (Press any key to exit.)'.format(int(wait_per_choice / 60))
                    logger.info(msg)
                    total_wait_for_choices += wait_per_choice
                    time.sleep(wait_per_choice)
                else:
                    msg = 'Processing complete. (No more choices)'
                    logger.info(msg)

                    msg = 'Choices reset. Start over.'
                    logger.info(msg)
        except KeyboardInterrupt:
            msg = 'KeyboardInterrupt.'
            logger.info(msg)
            sys.exit()
        except Exception as ex:
            extype, ex, tb = sys.exc_info()
            formatted = traceback.format_exception_only(extype, ex)[-1]
            for l in traceback.format_exception(extype, ex, tb):
                logger.error(l.rstrip())
            sys.exit()

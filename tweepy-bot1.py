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

production_token = 'production'

__production__ = any([arg == production_token for arg in sys.argv])

production_token = production_token if (__production__) else 'development'

base_filename = os.path.splitext(os.path.basename(__file__))[0]

log_filename = '{}{}{}{}{}{}{}_{}.log'.format('logs', os.sep, base_filename, os.sep, production_token, os.sep, base_filename, default_timestamp(datetime.utcnow()))

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
like_own_tweets = 'like_own_tweets'


articles_list = 'articles_list'
get_the_real_list = 'get_the_real_list'
update_the_article = 'update_the_article'
update_the_plan = 'update_the_plan'
get_articles = 'get_articles'
get_a_choice = 'get_a_choice'
get_more_followers = 'get_more_followers'


word_cloud = 'word_cloud'
get_final_word_cloud = 'get_final_word_cloud'
store_one_hashtag = 'store_one_hashtag'

if (not __production__):
    pylib = '/home/raychorn/projects/python-projects/private_vyperlogix_lib3'
    if (not any([f == pylib for f in sys.path])):
        print('Adding {}'.format(pylib))
        sys.path.insert(0, pylib)
    
from vyperlogix.enum import Enum
from vyperlogix.misc import _utils
from vyperlogix.env import environ
from vyperlogix.plugins import handler as plugins_handler

from vyperlogix.threads import pooled
from vyperlogix.decorators import interval
from vyperlogix.decorators import executor

class TheOptions(Enum.EnumMetaClass):
    use_local = 0
    master_list = 1
    use_cluster = 2
    use_cosmos1 = 4
    
def __escape(v):
    from urllib import parse
    return parse.quote_plus(v)

def __unescape(v):
    from urllib import parse
    return parse.unquote_plus(v)


__env__ = {}
env_literals = __env__.get('__LITERALS__', '').split('|')
def get_environ_keys(*args, **kwargs):
    from expandvars import expandvars
    
    k = kwargs.get('key')
    v = kwargs.get('value')
    assert (k is not None) and (v is not None), 'Problem with kwargs -> {}, k={}, v={}'.format(kwargs,k,v)
    __logger__ = kwargs.get('logger')
    v = expandvars(v) if (k not in env_literals) else v
    v = __escape(v) if (k in __env__.get('__ESCAPED__', '').split('|')) else v
    environ = kwargs.get('environ', {})
    ignoring = __env__.get('IGNORING', '').split('|')
    environ[k] = str(v)
    if (k not in ignoring):
        __env__[k] = str(v)
    if (__logger__):
        __logger__.info('\t{} -> {}'.format(k, environ.get(k)))
    return True

if (not __production__):
    env_path = '/home/raychorn/projects/python-projects/tweepy-twitter-bot1/.env'
else:
    env_path = '/tweepy-twitter-bot1/.env'

environ.load_env(env_path=env_path, environ=os.environ, cwd=env_path, verbose=True, logger=logger, ignoring_re='.git|.venv|__pycache__', callback=lambda *args, **kwargs:get_environ_keys(args, **kwargs))

__env2__ = dict([tuple([k,v]) for k,v in __env__.items()])

__env2__['MONGO_URI'] = os.environ.get('MONGO_CLUSTER')
__env2__['MONGO_AUTH_MECHANISM'] = os.environ.get('MONGO_CLUSTER_AUTH_MECHANISM')

__env3__ = dict([tuple([k,v]) for k,v in __env__.items()])

__env3__['MONGO_URI'] = os.environ.get('COSMOS_URI')
__env3__['MONGO_AUTH_MECHANISM'] = os.environ.get('COSMOS_AUTH_MECHANISM')

for k in __env__.get('__ESCAPED__', '').split('|'):
    __env__[k] = __unescape(__env__.get(k, ''))

explainOptions = lambda x:'use_local' if (x == TheOptions.use_local) else 'master_list' if (x == TheOptions.master_list) else 'use_cluster' if (x == TheOptions.use_cluster) else 'use_cosmos1' if (x == TheOptions.use_cosmos1) else 'unknown'

__the_options__ = TheOptions.use_local if (os.environ.get('OPTIONS') == 'use_local') else TheOptions.master_list if (os.environ.get('OPTIONS') == 'master_list') else TheOptions.use_cluster if (os.environ.get('OPTIONS') == 'use_cluster') else TheOptions.use_cosmos1 if (os.environ.get('OPTIONS') == 'use_cosmos1') else TheOptions.use_local

logger.info('__the_options__ -> {} -> {}'.format(__the_options__, explainOptions(__the_options__)))

is_really_a_string = lambda s:s and len(s)

access_token = os.environ.get('access_token', __env__.get('access_token'))
access_token_secret = os.environ.get('access_token_secret', __env__.get('access_token_secret'))
consumer_key = os.environ.get('consumer_key', __env__.get('consumer_key'))
consumer_secret = os.environ.get('consumer_secret', __env__.get('consumer_secret'))

assert is_really_a_string(access_token), 'Missing access_token.'
assert is_really_a_string(access_token_secret), 'Missing access_token_secret.'
assert is_really_a_string(consumer_key), 'Missing consumer_key.'
assert is_really_a_string(consumer_secret), 'Missing consumer_secret.'

mongo_db_name = os.environ.get('mongo_db_name', __env__.get('mongo_db_name'))
mongo_articles_col_name = os.environ.get('mongo_articles_col_name', __env__.get('mongo_articles_col_name'))
mongo_articles_plan_col_name = os.environ.get('mongo_articles_plan_col_name', __env__.get('mongo_articles_plan_col_name'))
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


class TwitterPlan():
    def __init__(self, num_items=-1, secs_until_tomorrow_morning=-1):
        self.num_items = num_items
        self.secs_until_tomorrow_morning = secs_until_tomorrow_morning
        self.__wait_per_choice__ = self.secs_until_tomorrow_morning / self.num_items
        self.__real_list__ = {}
        self.__ts_tweeted_time__ = None
        self.__required_velocity__ = -1
        self.__wait_per_choice__ = -1
        self.__the_choice__ = None
        self.__the_rotation__ = []
        
    @property
    def real_list(self):
        return self.__real_list__
        
    @real_list.setter
    def real_list(self, items):
        ts = _utils.timeStamp(offset=0, use_iso=True)
        keys = sorted(self.__real_list__.keys(), key=lambda k:datetime.fromisoformat(k), reverse=True)
        n = 100 if (__production__) else 5
        if (len(keys) > n):
            del self.__real_list__[keys[0]]
        self.__real_list__[ts] = items
        
    @property
    def ts_tweeted_time(self):
        return self.__ts_tweeted_time__
        
    @ts_tweeted_time.setter
    def ts_tweeted_time(self, ts_time):
        self.__ts_tweeted_time__ = ts_time
        
    @property
    def required_velocity(self):
        return self.__required_velocity__
        
    @required_velocity.setter
    def required_velocity(self, value):
        self.__required_velocity__ = value
        
    @property
    def wait_per_choice(self):
        return self.__wait_per_choice__
        
    @wait_per_choice.setter
    def wait_per_choice(self, value):
        self.__wait_per_choice__ = value
        
    @property
    def the_choice(self):
        return self.__the_choice__
        
    @the_choice.setter
    def the_choice(self, value):
        self.__the_choice__ = value
        
    @property
    def the_rotation(self):
        return self.__the_rotation__
        
    @the_rotation.setter
    def the_rotation(self, value):
        self.__the_rotation__ = value
        
    def as_json_serializable(self):
        return self.__dict__


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
    
environ = lambda : __env__ if (__the_options__ is not TheOptions.use_cluster) else __env2__

if (__name__ == '__main__'):
    plugins_manager = plugins_handler.PluginManager(plugins, debug=True, logger=logger)
    service_runner = plugins_manager.get_runner()
    
    __followers_executor_running__ = True #not __production__
    __likes_executor_running__ = True #not __production__
    
    def __followers_callback__(*args, **kwargs):
        global __followers_executor_running__
        __followers_executor_running__ = False
    
    def __likes_callback__(*args, **kwargs):
        global __likes_executor_running__
        __likes_executor_running__ = False
        
    if (__the_options__ == TheOptions.use_cosmos1):
        ts_current_time = _utils.timeStamp(offset=0, use_iso=True)
        the_master_list = service_runner.exec(articles_list, get_articles, **plugins_handler.get_kwargs(_id=None, environ=__env2__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name))
        
        for anId in the_master_list: # store the article from the master database into the cosmos1 database. Does nothing if the article exists.
            item = service_runner.exec(articles_list, get_articles, **plugins_handler.get_kwargs(_id=anId, environ=__env2__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name))
            msg = 'Storing article in cosmos1: {}'.format(item.get('_id'))
            logger.info(msg)
            the_rotation = service_runner.exec(articles_list, update_the_article, **plugins_handler.get_kwargs(the_choice=None, environ=__env2__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, logger=logger, item=item, ts_current_time=ts_current_time))
    
    api = service_runner.exec(twitter_verse, get_api, **plugins_handler.get_kwargs(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_token, access_token_secret=access_token_secret, logger=logger))
    
    if (0):
        h = get_top_trending_hashtags(api)
        print(h)

    while(1):
        try:
            print('\n'*10)
            ts_current_time = _utils.timeStamp(offset=0, use_iso=True)
            msg = 'Current time: {}'.format(ts_current_time)
            logger.info(msg)

            if (0):
                today = _utils.today_utctime()
                secs_until_tomorrow_morning = ((24 - today.hour) * (60*60)) + ((59 - today.minute) * 60)
                tomorrow_morning = _utils.timeStamp(offset=secs_until_tomorrow_morning, use_iso=True)
                dt_tomorrow_morning = datetime.fromisoformat(tomorrow_morning)
                delta = max(dt_tomorrow_morning, today) - min(dt_tomorrow_morning, today)
            secs_until_tomorrow_morning = 24*60*60 #  max(delta.total_seconds(), secs_until_tomorrow_morning)

            print('\n'*2)

            if (__the_options__ == TheOptions.master_list):
                the_master_list = service_runner.exec(articles_list, get_articles, **plugins_handler.get_kwargs(_id=None, environ=__env2__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name))
                
                for anId in the_master_list: # store the article from the master database into the local database. Does nothing if the article exists.
                    item = service_runner.exec(articles_list, get_articles, **plugins_handler.get_kwargs(_id=anId, environ=__env2__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name))
                    msg = 'Storing article locally: {}'.format(item.get('url'))
                    logger.info(msg)
                    the_rotation = service_runner.exec(articles_list, update_the_article, **plugins_handler.get_kwargs(the_choice=None, environ=__env__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, logger=logger, item=item, ts_current_time=ts_current_time))

            the_list = service_runner.exec(articles_list, get_articles, **plugins_handler.get_kwargs(_id=None, environ=environ(), mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name))
            assert len(the_list) > 0, 'Nothing in the list.'
            
            wait_per_choice = secs_until_tomorrow_morning / len(the_list)
            msg = 'wait_per_choice: {}'.format(wait_per_choice)
            logger.info(msg)
            
            the_twitter_plan = TwitterPlan(len(the_list), secs_until_tomorrow_morning)
            
            ts_tweeted_time = _utils.timeStamp(offset=-wait_per_choice, use_iso=True)
            msg = 'Tweeted time:  {}'.format(ts_tweeted_time)
            logger.info(msg)
            
            the_twitter_plan.ts_tweeted_time = ts_tweeted_time

            if (__production__):
                if (not __followers_executor_running__):
                    __followers_executor__ = pooled.BoundedExecutor(1, 5, callback=__followers_callback__)
                    
                    @executor.threaded(__followers_executor__)
                    def go_get_more_followers(runtime=0):
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
                        service_runner.exec(twitter_verse, get_more_followers, **plugins_handler.get_kwargs(api=api, environ=environ(), service_runner=service_runner, hashtags=hashtags, silent=False, runtime=runtime, logger=logger))
                    go_get_more_followers(runtime=(wait_per_choice - 60))
                    __executor_running__ = True

            if (__production__):
                if (not __likes_executor_running__):
                    __likes_executor__ = pooled.BoundedExecutor(1, 5, callback=__likes_callback__)
                    
                    @executor.threaded(__likes_executor__)
                    def go_like_own_stuff(runtime=0):
                        service_runner.exec(twitter_verse, like_own_tweets, **plugins_handler.get_kwargs(api=api, environ=environ(), runtime=runtime, logger=logger))
                    go_like_own_stuff(runtime=(wait_per_choice - 60))
                    __likes_executor_running__ = True

            the_real_list = service_runner.exec(articles_list, get_the_real_list, **plugins_handler.get_kwargs(the_list=the_list, logger=logger, ts_tweeted_time=ts_tweeted_time, tweet_period_secs=wait_per_choice, environ=environ(), mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name))

            the_twitter_plan.real_list = the_real_list
            
            msg = '='*30
            logger.info(msg)

            msg = 'the_real_list has {} items and the_list has {} items.'.format(len(the_real_list), len(the_list))
            logger.info(msg)
            
            required_velocity = len(the_real_list)
            msg = 'required_velocity: {}'.format(required_velocity)
            logger.info(msg)

            the_twitter_plan.required_velocity = required_velocity
            wait_per_choice = the_twitter_plan.secs_until_tomorrow_morning / required_velocity
            if (not __production__):
                wait_per_choice = wait_per_choice / 100
            wait_per_choice = 60 if (wait_per_choice < 60) else wait_per_choice
            the_twitter_plan.wait_per_choice = wait_per_choice
            
            @interval.timer(wait_per_choice, run_once=True, blocking=True, logger=logger)
            def issue_tweet(aTimer, **kwargs):
                random.seed(int(time.time()))
                the_choice = service_runner.exec(articles_list, get_a_choice, **plugins_handler.get_kwargs(the_list=the_real_list, ts_current_time=ts_current_time, logger=logger))
                assert the_choice, 'Nothing in the list?  Please check.'
                the_twitter_plan.the_choice = the_choice
                if (__production__):
                    the_choice = the_choice.get('_id') if (the_choice is not None) and (not isinstance(the_choice, str)) else the_choice
                    item = service_runner.exec(articles_list, get_articles, **plugins_handler.get_kwargs(_id=the_choice, environ=environ(), mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name))
                    assert item, 'Did not retrieve an item for {}.'.format(item)
                    service_runner.exec(twitter_verse, do_the_tweet, **plugins_handler.get_kwargs(api=api, item=item, logger=logger))
                    the_rotation = service_runner.exec(articles_list, update_the_article, **plugins_handler.get_kwargs(the_choice=the_choice, environ=environ(), mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, logger=logger, item=item, ts_current_time=ts_current_time))
                    
                    msg = 'BEGIN: the_rotation'
                    logger.info(msg)
                    
                    for v in the_rotation:
                        msg = '\t{}'.format(v)
                        logger.info(msg)
                    msg = 'END!!! the_rotation'
                    logger.info(msg)
                    print('\n'*2)
                    if (api.is_rate_limit_blown):
                        if (logger):
                            logger.warning('Twitter rate limit was blown. Halting to sleep then begin again.')
                else:
                    the_rotation = the_choice.get('__rotation__', []) if (the_choice is not None) and (not isinstance(the_choice, str)) else []
                the_twitter_plan.the_rotation = the_rotation
                service_runner.exec(articles_list, update_the_plan, **plugins_handler.get_kwargs(the_plan=the_twitter_plan.as_json_serializable(), environ=environ(), mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_plan_col_name, logger=logger, ts_current_time=ts_current_time))
            issue_tweet()
            
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
        if (api.is_rate_limit_blown):
            if (logger):
                logger.warning('Twitter rate limit was blown. Restarting after sleeping...')
            time.sleep(3600)
            api = service_runner.exec(twitter_verse, get_api, **plugins_handler.get_kwargs(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_token, access_token_secret=access_token_secret, logger=logger))

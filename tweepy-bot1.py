import os
import sys
import time
import math
import enum
import random
import mujson as json
import pprint
import socket
import logging

from loguru import logger as smart_logger
from logging.handlers import RotatingFileHandler

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import traceback

from queue import Queue

from dotenv import find_dotenv

from datetime import datetime

is_really_something = lambda s,t:s and t(s)
something_greater_than_zero = lambda s:(s > 0)

default_timestamp = lambda t:t.isoformat().replace(':', '').replace('-','').split('.')[0]

is_uppercase = lambda ch:''.join([c for c in str(ch) if c.isupper()])

class TheRunMode(enum.Enum):
    development = 0
    production = 1
    prod_dev = 2


production_token = 'production'
development_token = 'development'

__production__ = any([arg == production_token for arg in sys.argv])

__run_mode__ = TheRunMode.production if (__production__) else TheRunMode.development

is_production = lambda : __run_mode__ in [TheRunMode.production, TheRunMode.prod_dev]
is_simulated_production = lambda : __run_mode__ in [TheRunMode.prod_dev]

__run_mode__ = TheRunMode.prod_dev if (socket.gethostname() == 'DESKTOP-JJ95ENL') else __run_mode__ # Comment this out for production deployment.

production_token = production_token if (is_production()) else development_token

assert (TheRunMode.production if (any([arg == production_token for arg in [production_token]])) else TheRunMode.development) == TheRunMode.production, 'Something wrong with production mode detection.'


def get_stream_handler(streamformat="%(asctime)s:%(levelname)s:%(message)s"):
    stream = logging.StreamHandler()
    stream.setLevel(logging.INFO if (not is_simulated_production()) else logging.DEBUG)
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

log_filename = '{}{}{}{}{}{}{}_{}.log'.format('logs', os.sep, base_filename, os.sep, production_token if (not is_simulated_production()) else development_token, os.sep, base_filename, default_timestamp(datetime.utcnow()))
log_filename = os.sep.join([os.path.dirname(__file__), log_filename])

if (is_simulated_production()):
    import shutil
    log_root = os.path.dirname(os.path.dirname(log_filename))
    for p in [production_token, development_token]:
        fp = os.sep.join([log_root, p])
        if (os.path.exists(fp)):
            shutil.rmtree(fp)

if not os.path.exists(os.path.dirname(log_filename)):
    os.makedirs(os.path.dirname(log_filename))

if (os.path.exists(log_filename)):
    os.remove(log_filename)

log_format = ('[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s')
logging.basicConfig(
    level=logging.DEBUG if (is_simulated_production()) else logging.INFO,
    format=log_format,
    filename=(log_filename),
)

logger = setup_rotating_file_handler(base_filename, log_filename, (1024*1024*1024), 10)
logger.addHandler(get_stream_handler())

json_path = os.sep.join([os.path.dirname(__file__), 'json', '{}_tweet-stats.json'.format(base_filename)])
json_final_path = os.sep.join([os.path.dirname(__file__), 'json', '{}_tweet-stats-final_{}.json'.format(base_filename, default_timestamp(datetime.utcnow()))])

twitter_verse = 'twitter_verse'
get_api = 'get_api'
do_the_tweet = 'do_the_tweet'
like_own_tweets = 'like_own_tweets'


articles_list = 'articles_list'
get_the_real_list = 'get_the_real_list'
update_the_article = 'update_the_article'
update_the_plan = 'update_the_plan'
analyse_the_plans = 'analyse_the_plans'
get_articles = 'get_articles'
get_a_choice = 'get_a_choice'
get_more_followers = 'get_more_followers'
reset_plans_for_choices = 'reset_plans_for_choices'
reset_article_plans = 'reset_article_plans'
twitterbot_accounts = 'twitterbot_accounts'
get_account_id = 'get_account_id'
get_Options = 'get_Options'


word_cloud = 'word_cloud'
get_final_word_cloud = 'get_final_word_cloud'
store_one_hashtag = 'store_one_hashtag'

try:
    from vyperlogix.misc import _utils
except ImportError:
    pylib = '/home/raychorn/projects/python-projects/private_vyperlogix_lib3'
    if (not any([f == pylib for f in sys.path])):
        print('Adding {}'.format(pylib))
        sys.path.insert(0, pylib)
    
from vyperlogix.misc import _utils
from vyperlogix.env.environ import MyDotEnv
from vyperlogix.plugins import handler as plugins_handler

from vyperlogix.threads import pooled
from vyperlogix.decorators import interval
from vyperlogix.decorators import executor

class TheOptions(enum.Enum):
    use_local = 0
    master_list = 1
    use_cluster = 2
    use_cosmos0 = 4
    
def __escape(v):
    from urllib import parse
    return parse.quote_plus(v)

def __unescape(v):
    from urllib import parse
    return parse.unquote_plus(v)


__env__ = {}
env_literals = []
def get_environ_keys(*args, **kwargs):
    #global env_literals
    from expandvars import expandvars
    
    k = kwargs.get('key')
    v = kwargs.get('value')
    assert (k is not None) and (v is not None), 'Problem with kwargs -> {}, k={}, v={}'.format(kwargs,k,v)
    __logger__ = kwargs.get('logger')
    if (k == '__LITERALS__'):
        for item in v:
            env_literals.append(item)
    if (isinstance(v, str)):
        v = expandvars(v) if (k not in env_literals) else v
        v = __escape(v) if (k in __env__.get('__ESCAPED__', [])) else v
    ignoring = __env__.get('IGNORING', [])
    environ = kwargs.get('environ', None)
    if (isinstance(environ, dict)):
        environ[k] = v
    if (k not in ignoring):
        __env__[k] = v
    if (__logger__):
        __logger__.info('\t{} -> {}'.format(k, environ.get(k)))
    return tuple([k,v])

dotenv = MyDotEnv(find_dotenv(), verbose=True, interpolate=True, override=True, logger=logger, callback=get_environ_keys)
dotenv.set_as_environment_variables()

for k in __env__.get('__ESCAPED__', ''):
    __env__[k] = __unescape(__env__.get(k, ''))

__env2__ = dict([tuple([k,v]) for k,v in __env__.items()])
__env2__['MONGO_URI'] = os.environ.get('MONGO_CLUSTER')
__env2__['MONGO_AUTH_MECHANISM'] = os.environ.get('MONGO_CLUSTER_AUTH_MECHANISM')


__env3__ = dict([tuple([k,v]) for k,v in __env__.items()])
__env3__['MONGO_URI'] = os.environ.get('COSMOSDB0')
__env3__['MONGO_AUTH_MECHANISM'] = os.environ.get('COSMOS_AUTH_MECHANISM')


__env4__ = dict([tuple([k,v]) for k,v in __env3__.items()])
__env4__['MONGO_URI'] = os.environ.get('COSMOSDB1')

def __getattr(name, default=None):
    this_module = sys.modules[__name__]
    return getattr(this_module, name, default)
__mirrors__ = [__getattr(m, {}) for m in os.environ.get('MIRRORS', [])]

explainOptions = lambda x:str(x)

__the_options__ = TheOptions.use_local if (os.environ.get('OPTIONS') == 'use_local') else TheOptions.master_list if (os.environ.get('OPTIONS') == 'master_list') else TheOptions.use_cluster if (os.environ.get('OPTIONS') == 'use_cluster') else TheOptions.use_cosmos0 if (os.environ.get('OPTIONS') == 'use_cosmos0') else TheOptions.use_cosmos1 if (os.environ.get('OPTIONS') == 'use_cosmos1') else TheOptions.use_local

if (__run_mode__ == TheRunMode.prod_dev):
    __the_options__ = TheOptions.use_local

logger.info('__the_options__ -> {} -> {}'.format(__the_options__, explainOptions(__the_options__)))

is_really_a_string = lambda s:(s is not None) and (len(s) > 0)

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


mongo_twitterbot_db_name = os.environ.get('mongo_twitterbot_db_name', __env__.get('mongo_twitterbot_db_name'))
mongo_articles_list_col_name = os.environ.get('mongo_articles_list_col_name', __env__.get('mongo_articles_list_col_name'))
mongo_articles_plans_col_name = os.environ.get('mongo_articles_plans_col_name', __env__.get('mongo_articles_plans_col_name'))
mongo_twitterbot_account_col_name = os.environ.get('mongo_twitterbot_account_col_name', __env__.get('mongo_twitterbot_account_col_name'))

assert is_really_a_string(mongo_twitterbot_db_name), 'Missing mongo_twitterbot_db_name.'

assert is_really_a_string(mongo_articles_list_col_name), 'Missing mongo_articles_list_col_name.'
assert is_really_a_string(mongo_articles_plans_col_name), 'Missing mongo_articles_plans_col_name.'


plugins = __env__.get('plugins')
assert is_really_a_string(plugins) and os.path.exists(plugins), 'Missing plugins.'

if (0):
    from tweepy import binder
    m = sys.modules.get('tweepy.binder')
    assert m is not None, 'Problems with tweepy.binder.'
    def my_bind_api(*args, **kwargs):
        print()
    setattr(m, 'bind_api', my_bind_api)

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
        self.__the_process__ = {}
        
    @property
    def real_list(self):
        return self.__real_list__
        
    @real_list.setter
    def real_list(self, items):
        ts = _utils.timeStamp(offset=0, use_iso=True)
        keys = sorted(self.__real_list__.keys(), key=lambda k:datetime.fromisoformat(k), reverse=True)
        n = 100 if (is_production()) else 5
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
        
    @property
    def the_process(self):
        return self.__the_process__
        
    @the_process.setter
    def the_process(self, value):
        self.__the_process__ = value
        
    def as_json_serializable(self):
        return self.__dict__


class TwitterBotAccount():
    def __init__(self, tenant_id=None, service_runner=None, environ=None, logger=None):
        self.__logger__ = logger
        self.__tenant_id__ = tenant_id
        self.__environ__ = environ
        self.__service_runner__ = service_runner
        self.__account_cache__ = {}
        
    @property
    def account_cache(self):
        return self.__account_cache__
    
    @property
    def logger(self):
        return self.__logger__
    
    @logger.setter
    def logger(self, value):
        self.__logger__ = value

    @property
    def service_runner(self):
        return self.__service_runner__
    
    @service_runner.setter
    def service_runner(self, value):
        self.__service_runner__ = value

    @property
    def environ(self):
        return self.__environ__
    
    @environ.setter
    def environ(self, value):
        self.__environ__ = value

    @property
    def tenant_id(self):
        from bson.objectid import ObjectId
        
        doc = self.account_cache.get(self.__tenant_id__)
        __id = doc.get("_id") if (doc) else None
        if (not isinstance(__id, ObjectId)):
            doc = self.service_runner.exec(twitterbot_accounts, get_account_id, **plugins_handler.get_kwargs(environ=self.environ, tenant_id=self.__tenant_id__, mongo_db_name=self.mongo_db_name, mongo_col_name=mongo_twitterbot_account_col_name, logger=logger))
            __id = doc.get("_id") if (doc) else None
            if (isinstance(__id, ObjectId)):
                self.account_cache[self.__tenant_id__] = doc
            else:
                return None
        return self.__tenant_id__
    
    @property
    def account(self):
        from bson.objectid import ObjectId
        
        doc = self.account_cache.get(self.__tenant_id__, {})
        __id = doc.get("_id") if (doc) else None
        if (isinstance(__id, ObjectId)):
            return doc
        return None
    
    @property
    def mongo_db_name(self):
        return mongo_twitterbot_db_name if (is_really_a_string(self.__tenant_id__)) else mongo_db_name
    
    @property
    def mongo_articles_col_name(self):
        return mongo_articles_list_col_name if (is_really_a_string(self.__tenant_id__)) else mongo_articles_col_name
    
    @property
    def mongo_twitterbot_account_col_name(self):
        return mongo_twitterbot_account_col_name if (is_really_a_string(self.__tenant_id__)) else mongo_twitterbot_account_col_name
    
    @property
    def mongo_articles_plan_col_name(self):
        return mongo_articles_plans_col_name if (is_really_a_string(self.__tenant_id__)) else mongo_articles_plan_col_name
    
    

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

__vector__ = {}

twitter_bot_account = TwitterBotAccount(tenant_id=os.environ.get('__tenant__'), logger=logger)

__tweet_stats__ = {}

def save_tweet_stats(fpath, data, logger=None):
    def eat_numbers_from_end(value):
        while(1):
            if (len(value) > 0) and (value[-1].isdigit()):
                value = value[0:-1]
            else:
                break
        return value
    try:
        with open(fpath, 'w') as fOut:
            print(json.dumps(data, indent=3), file=fOut)
        file_tags = [''] + [int(n+1) for n in range(0,5)]
        file_parts = os.path.splitext(fpath)
        new_filename = file_parts[0]+str(file_tags[-1]) + file_parts[-1]
        if (os.path.exists(new_filename)):
            os.remove(new_filename)
        file_tags.reverse()
        __files = []
        for ft in file_tags:
            old_filename = file_parts[0]+str(ft) + file_parts[-1]
            if (os.path.exists(old_filename)):
                __files.append(old_filename)
        for fp in __files:
            ft = None
            old_filename = fp
            file_parts = os.path.splitext(old_filename)
            ch = str(file_parts[0][-1])
            if (ch.isdigit()):
                ft = int(ch)
            new_filename = eat_numbers_from_end(file_parts[0])+str(ft+1 if (isinstance(ft, int)) else 1) + file_parts[-1]
            if (os.path.exists(old_filename)):
                os.rename(old_filename, new_filename)
    except Exception as ex:
        extype, ex, tb = sys.exc_info()
        for l in traceback.format_exception(extype, ex, tb):
            logger.error(l.rstrip())
    return


@smart_logger.catch
def main_loop(max_tweets=None, debug=False, logger=None):
    plugins_manager = plugins_handler.SmartPluginManager(plugins, debug=True, logger=logger)
    service_runner = plugins_manager.get_runner()
    
    twitter_bot_account.service_runner = service_runner
    twitter_bot_account.environ = __env__ if (is_simulated_production() or (__the_options__ == TheOptions.use_local)) else __env2__ if (__the_options__ == TheOptions.use_cluster) else __env3__ if (__the_options__ == TheOptions.use_cosmos0) else None

    assert is_really_a_string(twitter_bot_account.tenant_id), 'Missing the twitter_bot_account.tenant_id.'
    
    service_runner.allow(articles_list, get_Options)
    Options = service_runner.articles_list.get_Options(**plugins_handler.get_kwargs())

    #_options__ = Options.do_nothing
    #__options__ = Options.init_articles
    __options__ =  Options.do_analysis
    #__options__ =  Options.do_reset
    
    __followers_executor_running__ = True #not __production__
    __likes_executor_running__ = True #not __production__
    
    def __followers_callback__(*args, **kwargs):
        global __followers_executor_running__
        __followers_executor_running__ = False
    
    def __likes_callback__(*args, **kwargs):
        global __likes_executor_running__
        __likes_executor_running__ = False
        
    
    def __backup_callback__(*args, **kwargs):
        logger.info('Backup done.')


    if (is_simulated_production()):
        # Perform analysis to determine usage stats
        if (__options__ == Options.do_analysis) or (__options__ == Options.do_reset):
            service_runner.allow(articles_list, analyse_the_plans)
            service_runner.articles_list.analyse_the_plans(**plugins_handler.get_kwargs(environ=__env__, twitter_bot_account=twitter_bot_account, json_path=json_final_path, options=__options__, logger=logger))
            return
        
        #service_runner.allow(articles_list, reset_article_plans)
        #the_plan = service_runner.articles_list.reset_article_plans(**plugins_handler.get_kwargs(environ=__env__, twitter_bot_account=twitter_bot_account, logger=logger))

    service_runner.allow(articles_list, get_articles)
    service_runner.allow(articles_list, update_the_article)

    if (__options__ == Options.init_articles): # copy articles into the new tenant structure.
        the_master_list = service_runner.articles_list.get_articles(**plugins_handler.get_kwargs(_id=None, environ=__env2__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, logger=logger))

        removes = ['__rotation__', '__rotation_processor__', 'debug']
        for anId in the_master_list: # store the article from the master database into the local database. Does nothing if the article exists.
            item = service_runner.articles_list.get_articles(**plugins_handler.get_kwargs(_id=anId, environ=__env2__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, logger=logger))
            for r in removes:
                if (r in item.keys()):
                    del item[r]
            service_runner.articles_list.update_the_article(**plugins_handler.get_kwargs(the_choice=None, environ=__env__, tenant_id=twitter_bot_account.tenant_id, mongo_db_name=twitter_bot_account.mongo_db_name, mongo_articles_col_name=twitter_bot_account.mongo_articles_col_name, logger=logger, item=item, ts_current_time=None))


    __backup_executor__ = pooled.BoundedExecutor(1, 5, callback=__backup_callback__)

    @executor.threaded(__backup_executor__)
    def backup_master_list():
        if (logger):
            logger.info('backup_master_list BEGIN:')
        if (os.environ.get('COSMOSDB0') or os.environ.get('COSMOSDB1')):
            ts_current_time = _utils.timeStamp(offset=0, use_iso=True)
            service_runner.allow(articles_list, get_articles)
            the_master_list = service_runner.articles_list.get_articles(**plugins_handler.get_kwargs(_id=None, environ=__env2__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, logger=logger))
                
            
            for anId in the_master_list: # store the article from the master database into the cosmos1 database. Does nothing if the article exists.
                item = service_runner.exec(articles_list, get_articles, **plugins_handler.get_kwargs(_id=anId, environ=__env2__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, logger=logger))
                msg = 'Storing article in {}: {}'.format(__the_options__, item.get('_id'))
                logger.info(msg)
                # Replicate the data with no actual update.
                if (os.environ.get('COSMOSDB0')):
                    the_rotation = service_runner.exec(articles_list, update_the_article, **plugins_handler.get_kwargs(the_choice=None, environ=__env3__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, logger=logger, item=item, ts_current_time=ts_current_time))
                if (os.environ.get('COSMOSDB1')):
                    the_rotation = service_runner.exec(articles_list, update_the_article, **plugins_handler.get_kwargs(the_choice=None, environ=__env4__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, logger=logger, item=item, ts_current_time=ts_current_time))
        if (logger):
            logger.info('backup_master_list END!!!')
        
        
    # Replicate the data from the Mongo Clusdter to Cosmos DB #0
    api = service_runner.exec(twitter_verse, get_api, **plugins_handler.get_kwargs(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_token, access_token_secret=access_token_secret, logger=logger))
    
    if (0):
        h = get_top_trending_hashtags(api)
        print(h)

    num_tweets = 0
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
                the_master_list = service_runner.exec(articles_list, get_articles, **plugins_handler.get_kwargs(_id=None, environ=__env2__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, logger=logger))
                
                for anId in the_master_list: # store the article from the master database into the local database. Does nothing if the article exists.
                    item = service_runner.exec(articles_list, get_articles, **plugins_handler.get_kwargs(_id=anId, environ=__env2__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, logger=logger))
                    msg = 'Storing article locally: {}'.format(item.get('url'))
                    logger.info(msg)
                    the_rotation = service_runner.exec(articles_list, update_the_article, **plugins_handler.get_kwargs(the_choice=None, environ=__env__, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, logger=logger, item=item, ts_current_time=ts_current_time))

            the_list = service_runner.articles_list.get_articles(**plugins_handler.get_kwargs(_id=None, environ=environ(), tenant_id=twitter_bot_account.tenant_id, mongo_db_name=twitter_bot_account.mongo_db_name, mongo_articles_col_name=twitter_bot_account.mongo_articles_col_name, logger=logger))
            assert len(the_list) > 0, 'Nothing in the list.'
            
            wait_per_choice = secs_until_tomorrow_morning / len(the_list)
            msg = 'wait_per_choice: {}'.format(wait_per_choice)
            logger.info(msg)
            
            the_twitter_plan = TwitterPlan(len(the_list), secs_until_tomorrow_morning)
            
            ts_tweeted_time = _utils.timeStamp(offset=-wait_per_choice, use_iso=True)
            msg = 'Tweeted time:  {}'.format(ts_tweeted_time)
            logger.info(msg)
            
            the_twitter_plan.ts_tweeted_time = ts_tweeted_time

            if (is_production()):
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
                    #go_get_more_followers(runtime=(wait_per_choice - 60))
                    #__executor_running__ = True

            if (is_production()):
                if (not __likes_executor_running__):
                    __likes_executor__ = pooled.BoundedExecutor(1, 5, callback=__likes_callback__)
                    
                    @executor.threaded(__likes_executor__)
                    def go_like_own_stuff(runtime=0):
                        service_runner.exec(twitter_verse, like_own_tweets, **plugins_handler.get_kwargs(api=api, environ=environ(), runtime=runtime, logger=logger))
                    go_like_own_stuff(runtime=(wait_per_choice - 60))
                    __likes_executor_running__ = True

            the_real_list = the_list # service_runner.exec(articles_list, get_the_real_list, **plugins_handler.get_kwargs(the_list=the_list, ts_tweeted_time=ts_tweeted_time, tweet_period_secs=wait_per_choice, environ=environ(), mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, logger=logger))

            #the_twitter_plan.real_list = the_real_list
            
            msg = '='*30
            logger.info(msg)

            msg = 'the_real_list has {} items and the_list has {} items.'.format(len(the_real_list), len(the_list))
            logger.info(msg)
            
            required_velocity = len(the_real_list)
            msg = 'required_velocity: {}'.format(required_velocity)
            logger.info(msg)

            the_twitter_plan.required_velocity = required_velocity
            wait_per_choice = the_twitter_plan.secs_until_tomorrow_morning / required_velocity
            if (is_simulated_production()):
                wait_per_choice = 1
            else:
                wait_per_choice = 60 if (wait_per_choice < 60) else wait_per_choice
            the_twitter_plan.wait_per_choice = wait_per_choice
            
            @interval.timer(wait_per_choice, no_initial_wait=False, run_once=True, blocking=True, logger=logger)
            def issue_tweet(aTimer, **kwargs):
                random.seed(int(time.time()))
                service_runner.allow(articles_list, get_a_choice)
                the_choice = service_runner.articles_list.get_a_choice(**plugins_handler.get_kwargs(the_list=the_real_list, twitter_bot_account=twitter_bot_account, ts_current_time=ts_current_time, this_process=the_twitter_plan.the_process, environ=environ(), tenant_id=twitter_bot_account.tenant_id, mongo_db_name=twitter_bot_account.mongo_db_name, mongo_articles_col_name=twitter_bot_account.mongo_articles_plan_col_name, logger=logger))
                if (the_choice is None):
                    service_runner.exec(articles_list, reset_plans_for_choices, **plugins_handler.get_kwargs(the_list=the_real_list, ts_current_time=ts_current_time, environ=environ(), tenant_id=twitter_bot_account.tenant_id, mongo_db_name=twitter_bot_account.mongo_db_name, mongo_articles_col_name=twitter_bot_account.mongo_articles_col_name, logger=logger))
                assert the_choice, 'Nothing in the list?  Please check.'
                the_twitter_plan.the_choice = the_choice
                if (is_production()):
                    the_choice = the_choice.get('_id') if (the_choice is not None) and (not isinstance(the_choice, str)) else the_choice
                    service_runner.allow(articles_list, get_articles)
                    item = service_runner.articles_list.get_articles(**plugins_handler.get_kwargs(_id=the_choice, environ=environ(), tenant_id=twitter_bot_account.tenant_id, mongo_db_name=twitter_bot_account.mongo_db_name, mongo_articles_col_name=twitter_bot_account.mongo_articles_col_name, logger=logger))
                    assert item, 'Did not retrieve an item for {}.'.format(item)
                    if (not is_simulated_production()):
                        service_runner.exec(twitter_verse, do_the_tweet, **plugins_handler.get_kwargs(api=api, item=item, logger=logger))
                    else:
                        __tweet_stats__[the_choice] = __tweet_stats__.get(the_choice, {})
                        __tweet_stats__[the_choice][ts_current_time] = __tweet_stats__[the_choice].get(ts_current_time, 0) + 1
                        save_tweet_stats(json_path, __tweet_stats__, logger=logger)
                        if (logger):
                            logger.debug('Simulated Tweet: {} -> {}'.format(the_choice, item.get('name')))

                service_runner.allow(articles_list, update_the_plan)
                service_runner.articles_list.update_the_plan(**plugins_handler.get_kwargs(tweet_stats=__tweet_stats__, environ=environ(), twitter_bot_account=twitter_bot_account, logger=logger))
                
                backup_last_run = __vector__.get('backup_last_run')
                if (logger):
                    logger.info('(1) backup_last_run -> {}'.format(backup_last_run))
                if (not backup_last_run):
                    __vector__['backup_last_run'] = _utils.timeStamp(offset=0, use_iso=True)
                    if (logger):
                        logger.info('(2) backup_last_run -> {}'.format(backup_last_run))
                    #backup_master_list()
                else:
                    dt = datetime.fromisoformat(backup_last_run)
                    period_secs = 60*60
                    one_hour_ago = datetime.fromisoformat(_utils.timeStamp(offset=-period_secs, use_iso=True))
                    delta = dt - one_hour_ago
                    __is__ = delta.total_seconds() > period_secs
                    if (__is__):
                        __vector__['backup_last_run'] = _utils.timeStamp(offset=0, use_iso=True)
                    if (logger):
                        logger.info('(3) backup_last_run -> {}'.format(backup_last_run))
                        #backup_master_list()
            issue_tweet()
            if (isinstance(max_tweets, int)) and (is_simulated_production()):
                num_tweets += 1
                if (num_tweets > max_tweets):
                    if (logger):
                        logger.info('DONE: num_tweets -> {}, max_tweets -> {}'.format(num_tweets, max_tweets))
                    break
            if (logger):
                logger.info('INFO: num_tweets -> {}, max_tweets -> {}'.format(num_tweets, max_tweets))
            
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
        if (not is_simulated_production()):
            if (api.is_rate_limit_blown):
                if (logger):
                    logger.warning('Twitter rate limit was blown. Restarting after sleeping...')
                time.sleep(3600)
                api = service_runner.exec(twitter_verse, get_api, **plugins_handler.get_kwargs(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_token, access_token_secret=access_token_secret, logger=logger))


if (__name__ == '__main__'):
    max_tweets = None
    if (is_simulated_production()):
        max_tweets = 1000
    main_loop(max_tweets=max_tweets, debug=True, logger=logger)

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

twitter_verse = 'twitter_verse'
get_api = 'get_api'
do_the_tweet = 'do_the_tweet'

articles_list = 'articles_list'
get_the_real_list = 'get_the_real_list'
update_the_article = 'update_the_article'

pylib = '/home/raychorn/projects/python-projects/private_vyperlogix_lib3/zips/vyperlogix39.zip'
if (not any([f == pylib for f in sys.path])):
    print('Adding {}'.format(pylib))
    sys.path.insert(0, pylib)
    
from vyperlogix.misc import _utils
from vyperlogix.env import environ

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

is_really_a_string = lambda s:s and len(s)

access_token = os.environ.get('access_token')
access_token_secret = os.environ.get('access_token_secret')
consumer_key = os.environ.get('consumer_key')
consumer_secret = os.environ.get('consumer_secret')

assert is_really_a_string(access_token), 'Missing access_token.'
assert is_really_a_string(access_token_secret), 'Missing access_token_secret.'
assert is_really_a_string(consumer_key), 'Missing consumer_key.'
assert is_really_a_string(consumer_secret), 'Missing consumer_secret.'

__domain__ = os.environ.get('__domain__')
__uuid__ = os.environ.get('__uuid__')

assert is_really_a_string(__domain__), 'Missing __domain__.'
assert is_really_a_string(__uuid__), 'Missing __uuid__.'

mongo_db_name = os.environ.get('mongo_db_name')
mongo_articles_col_name = os.environ.get('mongo_articles_col_name')
mongo_article_text_col_name = os.environ.get('mongo_article_text_col_name')
mongo_words_col_name = os.environ.get('mongo_words_col_name')
mongo_cloud_col_name = os.environ.get('mongo_cloud_col_name')

assert is_really_a_string(mongo_db_name), 'Missing mongo_db_name.'
assert is_really_a_string(mongo_articles_col_name), 'Missing mongo_articles_col_name.'
assert is_really_a_string(mongo_article_text_col_name), 'Missing mongo_article_text_col_name.'
assert is_really_a_string(mongo_words_col_name), 'Missing mongo_words_col_name.'
assert is_really_a_string(mongo_cloud_col_name), 'Missing mongo_cloud_col_name.'


plugins = os.environ.get('plugins')
assert is_really_a_string(plugins) and os.path.exists(plugins), 'Missing plugins.'



class ServiceRunner():
    '''
    Performs discovery and collects functions from the modules.
    '''
    def __init__(self, root,  debug=False, logger=None):
        self.root = root
        self.logger = logger
        self.debug = debug
        self.module_names = []
        if (not isinstance(self.root, list)):
            self.root = [self.root]
        self.__modules__ = {}
        for root in self.root:
            __is__ = False
            for f in sys.path:
                if (f == root):
                    __is__ = True
                    break
            if (not __is__):
                sys.path.insert(0, root)
            if (os.path.exists(root) and os.path.isdir(root)):
                module_names = [os.sep.join([root, f]) for f in os.listdir(root) if (not (os.path.splitext(f)[0] in ['__init__'])) and (os.path.splitext(f)[-1] in ['.py', '.pyc'])]
                for f in module_names:
                    self.module_names.append(f)
        
        for m in self.module_names:
            self.import_the_module_no_sandbox(m)


    @property
    def modules(self):
        return self.__modules__
    
    
    def __import_the_module__(self, m):
        import importlib
        root = 'exception'
        try:
            m_name = os.path.splitext(os.path.basename(m))[0]
            for root in self.root:
                full_module_name = '{}'.format(m_name)
                m1 = importlib.import_module(full_module_name)
                if (self.logger):
                    self.logger.info('\tm_name -> {}'.format(m_name))
                self.__modules__[root] = self.__modules__.get(root, {})
                self.__modules__.get(root, {})[m_name] = m1
        except Exception as ex:
            extype, ex, tb = sys.exc_info()
            if (self.debug):
                self.logger.error('BEGIN: Exception')
                for l in traceback.format_exception(extype, ex, tb):
                    print(l.rstrip())
                    self.logger.error(l.rstrip())
                self.logger.error('END!!! Exception')


    def import_the_module_no_sandbox(self, m):
        return self.__import_the_module__(m)
    

    def __exec_the_function__(self, f, *args, **kwargs):
        return f(args, kwargs)


    def exec_the_function_no_sandbox(self, f, *args, **kwargs):
        return self.__exec_the_function__(f, *args, **kwargs)
    

    def exec(self, module_name, func_name, *args, **kwargs):
        '''
        this method does not require any sandboxing because import sandbox limits the functions available which means
        there is no way for people to import anything potentially dangerous due to sandbox limits do nobody "can" do
        any dynamic imports via the exec method.
        '''
        import imp
        response = {}
        try:
            m = None
            for root in self.__modules__.keys():
                m = self.__modules__[root].get(module_name, None)
                if (m):
                    imp.reload(m)
                    break
            if (m is None):
                if (self.logger):
                    self.logger.info('*** {}.exec :: module_name -> {}'.format(self.__class__.__name__, module_name))
            f = getattr(m, func_name)
            response['{}.{}'.format(module_name, func_name)] = self.exec_the_function_no_sandbox(f, args, **kwargs)
        except Exception as ex:
            extype, ex, tb = sys.exc_info()
            formatted = traceback.format_exception_only(extype, ex)[-1]
            response['exception'] = formatted
            if (self.logger):
                self.logger.error('BEGIN: Exception')
                for l in traceback.format_exception(extype, ex, tb):
                    print(l.rstrip())
                    self.logger.error(l.rstrip())
                self.logger.error('END!!! Exception')
        return response



class PluginManager(object):

    def __init__(self, plugins, debug=False):
        self.plugins = plugins if (isinstance(plugins, list)) else [plugins]
        self.debug = debug


    @property
    def plugins(self):
        return self.__plugins__
    
    
    @plugins.setter
    def plugins(self, value):
        self.__plugins__ = value


    @property
    def debug(self):
        return self.__debug
    

    @debug.setter
    def debug(self, value):
        self.__debug = value


    def get_runner(self):
        __fp_plugins__ = self.plugins
        for fp_plugins in __fp_plugins__:
            has_plugins = os.path.exists(fp_plugins) and os.path.isdir(fp_plugins)
            if (not has_plugins):
                os.mkdir(fp_plugins)
                has_plugins = os.path.exists(fp_plugins) and os.path.isdir(fp_plugins)
            fp_plugins_initpy = os.sep.join([fp_plugins, '__init__.py'])
            if (not (os.path.exists(fp_plugins_initpy) and (os.path.isfile(fp_plugins_initpy)))):
                with open(fp_plugins_initpy, 'w') as fOut:
                    fOut.write('{}\n'.format('#'*40))
                    fOut.write('# (c). Copyright, Vyper Logix Corp, All Rights Reserved.\n')
                    fOut.write('{}\n'.format('#'*40))
                    fOut.write('\n\n')
                    fOut.flush()
        return ServiceRunner(__fp_plugins__,  logger=logger, debug=self.debug)



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
            try:
                d = dict([tuple(t.split('=')) for t in u.split('?')[-1].split('&')])
                k = d.get('source')
                v = d.get('sk')
                if (k and v):
                    data[k] = v
            except ValueError:
                pass
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
    
def log_traceback(ex, ex_traceback=None):
    if ex_traceback is None:
        ex_traceback = ex.__traceback__
    tb_lines = [ line.rstrip('\n') for line in
                traceback.format_exception(ex.__class__, ex, ex_traceback)]
    logger.critical(tb_lines)


if (__name__ == '__main__'):
    plugins_manager = PluginManager(plugins, debug=True)
    service_runner = plugins_manager.get_runner()
    
    api = service_runner.exec(twitter_verse, get_api, consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_token, access_token_secret=access_token_secret, logger=logger)
    
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
            
            the_real_list = service_runner.exec(articles_list, get_the_real_list, the_list=the_list, get_articles=__get_articles, ts_tweeted_time=ts_tweeted_time, tweet_period_secs=tweet_period_secs, logger=logger)
            msg = '='*30
            print(msg)
            logger.info(msg)

            msg = 'the_real_list has {} items and the_list has {} items.'.format(len(the_real_list), len(the_list))
            print(msg)
            logger.info(msg)
            
            required_velocity = math.ceil(len(the_list) / 24)
            
            the_chosen = set()
            random.seed(datetime.now())
            total_wait_for_choices = 0
            wait_per_choice = tweet_period_secs / int(required_velocity)
            for i in range(int(required_velocity)):
                l = list(set(the_real_list) - the_chosen)
                if (len(l) == 0):
                    break
                i_choice = max(random.randint(0, len(l)), len(l)-1)
                the_choice = l[i_choice if (len(l) > 0) else 0]
                print('the_choice: {}'.format(the_choice))
                
                the_chosen.add(the_choice)

                item = __get_articles(_id=the_choice)
                assert item, 'Did not retrieve an item for {}.'.format(the_choice)
                if (item):
                    service_runner.exec(twitter_verse, do_the_tweet, api=api, item=item, logger=logger)
                    the_rotation = service_runner.exec(articles_list, update_the_article, the_choice=the_choice, ts_current_time=ts_current_time, store_article_data=__store_article_data, item=item, logger=logger)
                    
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
                total_wait_for_choices += wait_per_choice
                time.sleep(wait_per_choice)
            if (tweet_period_secs - total_wait_for_choices) > 0:
                msg = 'Sleeping for {} mins. (Press any key to exit.)'.format(int((tweet_period_secs - total_wait_for_choices) / 60))
                print(msg)
                logger.info(msg)
                time.sleep(tweet_period_secs - total_wait_for_choices)
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

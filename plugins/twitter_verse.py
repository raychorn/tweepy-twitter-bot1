import os
import sys
import time
import tweepy

import traceback

from _tweepy.api import TweepyAPI

from vyperlogix.misc import _utils
from vyperlogix.decorators import args
from vyperlogix.plugins import handler as plugins_handler
from vyperlogix.misc import normalize_int_from_str, normalize_float_from_str

from vyperlogix.classes.MagicObject import MagicObject2

word_cloud = 'word_cloud'
get_final_word_cloud = 'get_final_word_cloud'
store_one_hashtag = 'store_one_hashtag'
get_hashtag_matching = 'get_hashtag_matching'
delete_all_hashtags = 'delete_all_hashtags'
delete_one_hashtag = 'delete_one_hashtag'
reset_all_hashtags = 'reset_all_hashtags'


last_followers = 'last_followers'

class TwitterAPIProxy(MagicObject2):
    def __init__(self, consumer_key=None, consumer_secret=None, access_token=None, access_token_secret=None, logger=None):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.logger = logger
        self.calls_count = 0
        self.start_time = time.time()
        self.rate_limit = normalize_float_from_str(os.environ.get('twitter_rate_limit', 0.25))
        assert self.rate_limit and (isinstance(self.rate_limit, float)) and (self.rate_limit > 0.0), 'Missing rate_limit.'
        self.rate_limit_stats = {}
        self.is_rate_limit_blown = False
        
        try:
            self.auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
            self.auth.set_access_token(self.access_token, self.access_token_secret)
            self.api = TweepyAPI(self.auth, wait_on_rate_limit=True)
            self.ingest_rate_limit_stats(self.api.rate_limit_status())
        except:
            msg = 'Problem connecting to the twitter?'
            if (logger):
                logger.exception(msg)
            sys.exit()
            
            
    def __refresh_rate_limits__(self):
        self.rate_limit_stats = {}
        self.ingest_rate_limit_stats(self.api.rate_limit_status())
        
    
    def __any_rate_limits_getting_low__(self, threshold):
        self.__refresh_rate_limits__()
        items = [i for i in list(self.rate_limit_stats.get('remaining', {}).keys())]
        return any([int(i) < threshold for i in items])


    def __call__(self,*args,**kwargs):
        self.n = [n for n in self.n if (n != '__iter__')]
        if (len(self.n) > 0):
            self.calls_count += 1
            # heuristic begins.
            et = time.time() - self.start_time
            v = self.calls_count / et
            if (self.logger):
                self.logger.info('Twitter rate limits? ({} calls in {} secs)  (v is {} of {})'.format(self.calls_count, et, v, self.rate_limit))
            if (v > self.rate_limit):
                while (v > self.rate_limit):
                    if (self.logger):
                        self.logger.info('Sleeping due to twitter rate limits. (v is {} of {})'.format(v, self.rate_limit))
                    time.sleep(1)
                    et = time.time() - self.start_time
                    v = self.calls_count / et
            # heuristic ends.
            method = self.n.pop()
            s = 'self.api.%s(*args,**kwargs)' % (method)
            if (self.logger):
                self.logger.info('{} {} ({}, {}s)'.format(self.__class__, s, args, kwargs))
            time.sleep(1.0)
            resp = None
            try:
                resp = eval(s)
            except tweepy.error.RateLimitError:
                self.is_rate_limit_blown = True
                if (self.logger):
                    self.logger.info('Sleeping for 30 secs due to rate limit issues.')
                time.sleep(30)
            return resp
        return None
    
    
    def ingest_rate_limit_stats(self, stats, ignoring=['labs', 'moments']):
        for category,cat_stats in stats.items():
            if (category not in ['rate_limit_context']):
                for subcat,subcat_stats in cat_stats.items():
                    for specific,specific_stats in subcat_stats.items():
                        if (subcat in ignoring):
                            continue
                        p = '{}:{}:{}'.format(category, subcat, specific)
                        for k,v in specific_stats.items():
                            bucket = self.rate_limit_stats.get(k, {})
                            subBucket = bucket.get(v, [])
                            subBucket.append(p)
                            bucket[v] = subBucket
                            self.rate_limit_stats[k] = bucket


def __get_api(consumer_key=None, consumer_secret=None, access_token=None, access_token_secret=None, logger=None):
    return TwitterAPIProxy(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_token, access_token_secret=access_token_secret, logger=logger)
    

@args.kwargs(__get_api)
def get_api(*args, **kwargs):
    pass

def __get_top_trending_hashtags(api):
    data = api.trends_place(1)
    hashtags = dict([tuple([trend['name'], trend['tweet_volume']]) for trend in data[0]['trends'] if (trend['name'].startswith('#')) and (len(_utils.ascii_only(trend['name'])) == len(trend['name']))])
    return _utils.sorted_dict(hashtags, reversed=True, default=-1)
    

def __get_shorter_url(url):
    from vyperlogix.bitly import shorten

    bitly_access_token = os.environ.get('bitly_access_token')
    assert bitly_access_token and (len(bitly_access_token) > 0), 'Missing the bitly_access_token. Check your .env file.'

    return shorten(url, token=bitly_access_token)


def __do_the_tweet(api=None, item=None, popular_hashtags=None, logger=None, silent=False):
    sample_tweet = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    url = item.get('url')
    assert url and (len(url) > 0), 'Problem with URL in do_the_tweet().'
    u = __get_shorter_url(url) if (len(url) > int(os.environ.get('minimum_url_length', 40))) else url
    msg = 'URL: {} -> {}'.format(url, u)
    if (logger):
        logger.info(msg)
    if (0):
        extra_domains = '(raychorn.github.io + raychorn.medium.com)\n'
        the_tweet = '{}\n{}\n{}'.format(item.get('name'), u, extra_domains)
    else:
        the_tweet = '{}\n{}\n'.format(item.get('name'), u)
    num_chars = len(sample_tweet) - len(the_tweet)
    popular_hashtags = __get_top_trending_hashtags(api) if (not popular_hashtags) else popular_hashtags
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
    if (logger):
        logger.info('BEGIN: TWEET')
        logger.info(the_tweet)
        logger.info('END!!! TWEET')
    if (not silent):
        tweet = api.update_status(the_tweet)
        try:
            tweet.favorite()
        except Exception as ex:
            extype, ex, tb = sys.exc_info()
            formatted = traceback.format_exception_only(extype, ex)[-1]
            if (logger):
                logger.error(formatted)


@args.kwargs(__do_the_tweet)
def do_the_tweet(*args, **kwargs):
    pass


def __handle_hashtags(service_runner=None, environ=None, logger=None, hashtags=[]):
    for hashtag in hashtags:
        doc = service_runner.exec(word_cloud, get_hashtag_matching, **plugins_handler.get_kwargs(hashtag=hashtag, environ=environ, logger=logger))
        if (not doc):
            count = service_runner.exec(word_cloud, store_one_hashtag, **plugins_handler.get_kwargs(data={'hashtag': hashtag}, environ=environ))
            assert count > -1, 'Problem with store_one_hashtag for {}.'.format(count)
            if (logger):
                logger.info('Added hashtag ("{}").'.format(hashtag))


def __handle_one_available_hashtag(api=None, service_runner=None, environ=None, logger=None):
    ts_follower_time = _utils.timeStamp(offset=0, use_iso=True)
    assert service_runner, 'Missing service_runner.'
    assert environ, 'Missing environ.'

    me = api.me()

    if (0):
        words = service_runner.exec(word_cloud, get_final_word_cloud, **plugins_handler.get_kwargs(environ=environ, callback=None, logger=logger))
        for k,v in words.get('word-cloud', {}).items():
            doc = service_runner.exec(word_cloud, get_hashtag_matching, **plugins_handler.get_kwargs(hashtag=k, environ=environ, logger=logger))
            if (doc) and (not doc.get(last_followers)):
                pass
            
    doc = service_runner.exec(word_cloud, get_hashtag_matching, **plugins_handler.get_kwargs(criteria={ last_followers : { "$exists": False } }, environ=environ, logger=logger))
    if (doc) and (not doc.get(last_followers)):
        hashtag = doc.get('hashtag')
        if (hashtag):
            hashtag_count = 0
            h = '{}{}'.format('#' if (hashtag.find('#') == -1) else '', hashtag)
            for tweeter in tweepy.Cursor(api.search, q=h).items():
                friends1 = api.show_friendship(source_screen_name=tweeter.screen_name, target_screen_name=me.screen_name)
                friends2 = api.show_friendship(source_screen_name=me.screen_name, target_screen_name=tweeter.screen_name)
                if (not any([f.following for f in friends1])) or (not any([f.following for f in friends2])):
                    api.create_friendship(screen_name=tweeter.screen_name)
                    hashtag_count += 1
                    time.sleep(environ.get('hashtags_followers_pace', 60))
                    if (logger):
                        logger.info('followed {}'.format(tweeter.screen_name))
                if (api.is_rate_limit_blown):
                    if (logger):
                        logger.info('Twitter rate limit was blown.')
                    break
            if (hashtag_count == 0):
                status = service_runner.exec(word_cloud, delete_one_hashtag, **plugins_handler.get_kwargs(environ=environ, hashtag=hashtag, logger=logger))
                assert status, 'Did not delete the hashtags {} for followers.'.format(hashtag)
                if (logger):
                    logger.warning('Resetting hashtags for new followers.')
    else:
        status = service_runner.exec(word_cloud, reset_all_hashtags, **plugins_handler.get_kwargs(environ=environ, attr=last_followers, logger=logger))
        assert status, 'Did not reset all the hashtags for followers.'
        if (logger):
            logger.warning('Resetting hashtags for new followers.')


def __get_more_followers(api=None, environ=None, service_runner=None, logger=None, hashtags=[], silent=False, runtime=0):
    '''
    This function was designed to be a long-running background task that seeks to add followers on a 24x7 basis based on the most popular hashtags.
    '''
    assert api, 'Missing api.'
    assert environ, 'Missing environ.'
    assert service_runner, 'Missing service_runner.'
    
    count = 0
    me = api.me()
    start_time = time.time()
    if (logger):
        logger.info('Started __get_more_followers')
    if (environ.get('twitter_follow_followers')):
        items = api.followers_ids(me.id)
        if (isinstance(items, list)):
            for anId in items:
                follower = api.get_user(anId)
                if (logger):
                    logger.info('Checking follower: {}'.format(follower.screen_name))
                friends = api.show_friendship(source_screen_name=follower.screen_name, target_screen_name=me.screen_name)
                time.sleep(1)
                friends2 = api.show_friendship(source_screen_name=me.screen_name, target_screen_name=follower.screen_name)
                time.sleep(1)
                if (not any([f.following for f in friends])) or (not any([f.following for f in friends2])):
                    count += 1
                    if (logger):
                        logger.info('follow the follower: {}'.format(follower.screen_name))
                    api.create_friendship(follower.id)
                if (api.is_rate_limit_blown):
                    if (logger):
                        logger.info('Twitter rate limit was blown.')
                    break
    most_popular_hashtags = __get_top_trending_hashtags(api)
    __handle_hashtags(service_runner=service_runner, environ=environ, hashtags=list(set(hashtags+most_popular_hashtags)), logger=logger)
    while (1):
        if (logger):
            logger.info('BEGIN: __handle_one_available_hashtag')
        __handle_one_available_hashtag(api=api, service_runner=service_runner, environ=environ, logger=logger)
        if (logger):
            logger.info('END!!! __handle_one_available_hashtag')

        if (logger):
            logger.info('runtime: {}'.format(runtime))
            
            
            
        if (runtime) and (isinstance(runtime, int)) and (runtime > 0):
            time_now = time.time()
            et = time_now - start_time
            if (logger):
                logger.info('et: {}, runtime: {}'.format(et, runtime))
            if (et > runtime):
                if (logger):
                    logger.info('et: {} is greater than runtime: {}'.format(et, runtime))
                break
        if (api.is_rate_limit_blown):
            if (logger):
                logger.info('Twitter rate limit was blown.')
            break
    if (count > 0):
        if (logger):
            logger.info('followed {} followers'.format(count))


@args.kwargs(__get_more_followers)
def get_more_followers(*args, **kwargs):
    pass


def __like_own_tweets(api=None, environ=None, logger=None, runtime=0):
    '''
    This function was designed to be a long-running background task that seeks to like my own tweets because who better to like my tweets.
    '''
    assert api, 'Missing api.'
    assert environ, 'Missing environ.'

    me = api.me()
    if (logger):
        logger.info('Started __like_own_tweets')
    tweets = api.user_timeline(screen_name=me.screen_name,count=100)
    for tweet in tweets:
        if (not tweet.favorited):
            tweet.favorite()
            if (logger):
                logger.info('liked {}'.format(tweet.text))
        if (api.is_rate_limit_blown):
            if (logger):
                logger.info('Twitter rate limit was blown.')
            break
    if (logger):
        logger.info('Completed __like_own_tweets')

@args.kwargs(__like_own_tweets)
def like_own_tweets(*args, **kwargs):
    pass

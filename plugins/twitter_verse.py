import os
import sys
import time
import tweepy

from vyperlogix.misc import _utils
from vyperlogix.decorators import args
from vyperlogix.plugins import handler as plugins_handler


word_cloud = 'word_cloud'
get_final_word_cloud = 'get_final_word_cloud'
store_one_hashtag = 'store_one_hashtag'
get_hashtag_matching = 'get_hashtag_matching'
delete_all_hashtags = 'delete_all_hashtags'
delete_one_hashtag = 'delete_one_hashtag'
reset_all_hashtags = 'reset_all_hashtags'


last_followers = 'last_followers'


def __get_api(consumer_key=None, consumer_secret=None, access_token=None, access_token_secret=None, logger=None):
    try:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
    except:
        msg = 'Problem connecting to the twitter?'
        if (logger):
            logger.error(msg)
        sys.exit()
    return api
    

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
        api.update_status(the_tweet)


@args.kwargs(__do_the_tweet)
def do_the_tweet(*args, **kwargs):
    pass


def __handle_hashtags(service_runner=None, environ=None, logger=None, hashtags=[]):
    if (1):
        docs = service_runner.exec(word_cloud, get_hashtag_matching, **plugins_handler.get_kwargs(environ=environ, logger=logger))
        print()
    for hashtag in hashtags:
        doc = service_runner.exec(word_cloud, get_hashtag_matching, **plugins_handler.get_kwargs(hashtag=hashtag, environ=environ, logger=logger))
        if (not doc):
            count = service_runner.exec(word_cloud, store_one_hashtag, **plugins_handler.get_kwargs(data={'hashtag': hashtag}, environ=environ))
            assert count > -1, 'Problem with store_one_hashtag for {}.'.format(count)


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
                friends = api.show_friendship(source_screen_name=tweeter.screen_name, target_screen_name=me.screen_name)
                if (not any([f.following for f in friends])):
                    api.create_friendship(screen_name=tweeter.screen_name)
                    hashtag_count += 1
                    time.sleep(environ.get('hashtags_followers_pace', 60))
                    if (logger):
                        logger.info('followed {}'.format(tweeter.screen_name))
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
    assert service_runner, 'Missing service_runner.'
    
    count = 0
    me = api.me()
    for follower in api.followers(me.screen_name):
        if (logger):
            logger.info('follower: {}'.format(follower.screen_name))
            friends = api.show_friendship(source_screen_name=follower.screen_name, target_screen_name=me.screen_name)
            if (not any([f.following for f in friends])):
                count += 1
                if (logger):
                    logger.info('follow the follower: {}'.format(follower.screen_name))
                api.create_friendship(follower.id)
    most_popular_hashtags = __get_top_trending_hashtags(api)
    __handle_hashtags(service_runner=service_runner, environ=environ, hashtags=list(set(hashtags+most_popular_hashtags)), logger=logger)
    start_time = time.time()
    while (1):
        __handle_one_available_hashtag(api=api, service_runner=service_runner, environ=environ, logger=logger)

        if (runtime) and (isinstance(runtime, int)) and (runtime > 0):
            time_now = time.time()
            et = time_now - start_time
            if (et > runtime):
                break
    if (count > 0):
        if (logger):
            logger.info('followed {} followers'.format(count))


@args.kwargs(__get_more_followers)
def get_more_followers(*args, **kwargs):
    pass


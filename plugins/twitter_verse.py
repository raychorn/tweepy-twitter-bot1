import os
import sys
import tweepy

from vyperlogix.misc import _utils
from vyperlogix.decorators import args


def __get_api(consumer_key=None, consumer_secret=None, access_token=None, access_token_secret=None, logger=None):
    try:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
    except:
        msg = 'Problem connecting to the twitter?'
        print(msg)
        if (logger):
            logger.error(msg)
        sys.exit()
    return api
    

@args.kwargs(__get_api)
def get_api(*args, **kwargs):
    pass

def get_top_trending_hashtags(api):
    data = api.trends_place(1)
    hashtags = dict([tuple([trend['name'], trend['tweet_volume']]) for trend in data[0]['trends'] if (trend['name'].startswith('#')) and (len(_utils.ascii_only(trend['name'])) == len(trend['name']))])
    return _utils.sorted_dict(hashtags, reversed=True, default=-1)
    

def get_shorter_url(url):
    from vyperlogix.bitly import shorten

    bitly_access_token = os.environ.get('bitly_access_token')
    assert bitly_access_token and (len(bitly_access_token) > 0), 'Missing the bitly_access_token. Check your .env file.'

    return shorten(url, token=bitly_access_token)


def do_the_tweet(p1={},p2={}):
    '''
    Called from outside this module because there are issues with the way kwargs are being used.
    '''
    d = p1 if (isinstance(p1, dict)) else p2 if (isinstance(p2, dict)) else None
    assert d, 'Missing parameters.'
    api = d.get('api')
    item = d.get('item', {})
    popular_hashtags = d.get('popular_hashtags', [])
    logger = d.get('logger')
    silent = d.get('silent', False)
    return __do_the_tweet(api=api, item=item, popular_hashtags=popular_hashtags, logger=logger, silent=silent)


def __do_the_tweet(api=None, item=None, popular_hashtags=None, logger=None, silent=False):
    sample_tweet = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    url = item.get('url')
    assert url and (len(url) > 0), 'Problem with URL in do_the_tweet().'
    u = get_shorter_url(url) if (len(url) > int(os.environ.get('minimum_url_length', 40))) else url
    msg = 'URL: {} -> {}'.format(url, u)
    print(msg)
    if (logger):
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
    if (logger):
        logger.info('BEGIN: TWEET')
        logger.info(the_tweet)
        logger.info('END!!! TWEET')
    if (not silent):
        api.update_status(the_tweet)


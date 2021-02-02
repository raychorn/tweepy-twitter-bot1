from datetime import datetime
from vyperlogix.misc import _utils

def get_the_real_list(the_list=[], get_articles=None, logger=None, ts_tweeted_time=_utils.timeStamp(offset=-(1*60*60), use_iso=True), tweet_period_secs=1*60*60):
    the_real_list = []
    for anId in the_list:
        item = get_articles(_id=anId) if (callable(get_articles)) else []
        if (item):
            sz = item.get('friends_link')
            tt = item.get('tweeted_time')
            msg = 'id: {}, sz: {}, tt: {}'.format(anId, sz, tt)
            print(msg)
            if (logger):
                logger.info(msg)
            
            if (tt is None):
                the_real_list.append(anId)
                msg = 'Added to the_real_list: {}\n'.format(anId)
                print(msg)
                if (logger):
                    logger.info(msg)
                continue
            
            dt_target = datetime.fromisoformat(ts_tweeted_time)
            dt_item = datetime.fromisoformat(tt)
            delta = max(dt_target, dt_item) - min(dt_target, dt_item)
            __is__ = delta.total_seconds() > tweet_period_secs
            msg = 'delta: {}, dt_target: {}, dt_item: {}, delta.total_seconds(): {}, tweet_period_secs: {}, __is__: {}'.format(delta, dt_target, dt_item, delta.total_seconds(), tweet_period_secs, __is__)
            print(msg)
            if (logger):
                logger.info(msg)
            
            if (__is__):
                the_real_list.append(anId)
                msg = 'Added to the_real_list: {}\n'.format(anId)
                print(msg)
                if (logger):
                    logger.info(msg)
                continue
    return the_real_list


def most_recent_30_days(bucket):
    period_secs = 30*24*60*60
    thirty_days_ago = _utils.timeStamp(offset=-period_secs, use_iso=True)
    new_bucket = []
    for ts_tweeted_time in bucket:
        dt = datetime.fromisoformat(ts_tweeted_time)
        delta = dt - thirty_days_ago
        __is__ = delta.total_seconds() < period_secs
        if (__is__):
            new_bucket.append(ts_tweeted_time)
    return new_bucket


def update_the_article(item=None, the_choice=None, ts_current_time=None, logger=None, store_article_data=None):
    assert item, 'Missing item.'
    assert the_choice, 'Missing the_choice.'
    assert ts_current_time, 'Missing ts_current_time.'
    assert callable(store_article_data), 'Missing callable store_article_data.'
    
    the_update = { 'tweeted_time': ts_current_time}

    __rotation__ = '__rotation__'
    bucket = item.get(__rotation__, [])
    bucket.append(ts_current_time)
    the_update[__rotation__] = most_recent_30_days(bucket)

    msg = 'Updating: id: {}, {}'.format(the_choice, the_update)
    print(msg)
    if (logger):
        logger.info(msg)
    resp = store_article_data(item, update=the_update)
    assert isinstance(resp, int), 'Problem with the response? Expected int value but got {}'.format(resp)
    print('Update was done.')
    
    return the_update[__rotation__]
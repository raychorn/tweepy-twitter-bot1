from datetime import datetime
from vyperlogix.misc import _utils
from bson.objectid import ObjectId
from vyperlogix.mongo import vyperapi
from vyperlogix.decorators import __with



def __get_articles(_id=None, environ=None, mongo_db_name=None, mongo_articles_col_name=None, criteria=None, callback=None):
    @__with.database(environ=environ)
    def db_get_articles(db=None, _id=None):
        mongo_db_name = environ.get('mongo_db_name')
        mongo_articles_col_name = environ.get('mongo_articles_col_name')
        assert vyperapi.is_not_none(db), 'There is no db.'
        assert vyperapi.is_not_none(mongo_db_name), 'There is no mongo_db_name.'
        assert vyperapi.is_not_none(mongo_articles_col_name), 'There is no mongo_articles_col_name.'

        tb_name = mongo_db_name
        col_name = mongo_articles_col_name
        table = db[tb_name]
        coll = table[col_name]

        find_in_collection = lambda c,criteria=criteria:c.find() if (not criteria) else c.find(criteria)
        recs = []
        _id = _id[0] if (isinstance(_id, tuple)) else _id
        if (not _id) or (_id == tuple([])):
            recs = [str(doc.get('_id')) for doc in find_in_collection(coll, criteria=criteria)]
        else:
            recs = coll.find_one({"_id": ObjectId(_id)})
        if (callable(callback)):
            callback(coll=coll, recs=recs, _id=_id)
        return recs
    return db_get_articles(_id=_id)


def get_articles(p1={},p2={}):
    '''
    Called from outside this module because there are issues with the way kwargs are being used.
    '''
    d = p1 if (isinstance(p1, dict)) else p2 if (isinstance(p2, dict)) else None
    assert d, 'Missing parameters.'
    _id = d.get('_id')
    environ = d.get('environ', {})
    mongo_db_name = d.get('mongo_db_name')
    mongo_articles_col_name = d.get('mongo_articles_col_name')
    criteria = d.get('criteria')
    callback = d.get('callback')
    return __get_articles(_id=_id, environ=environ, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, criteria=criteria, callback=callback)


def __store_article_data(data, environ=None, mongo_db_name=None, mongo_articles_col_name=None, update=None):
    @__with.database(environ=environ)
    def db_store_article_data(db=None, data=None):
        mongo_db_name = environ.get('mongo_db_name')
        mongo_articles_col_name = environ.get('mongo_articles_col_name')
        assert vyperapi.is_not_none(db), 'There is no db.'
        assert vyperapi.is_not_none(mongo_db_name), 'There is no mongo_db_name.'
        assert vyperapi.is_not_none(mongo_articles_col_name), 'There is no mongo_articles_col_name.'

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



def get_the_real_list(p1={},p2={}):
    '''
    Called from outside this module because there are issues with the way kwargs are being used.
    '''
    d = p1 if (isinstance(p1, dict)) else p2 if (isinstance(p2, dict)) else None
    assert d, 'Missing parameters.'
    the_list = d.get('the_list', [])
    logger = d.get('logger')
    ts_tweeted_time = d.get('ts_tweeted_time')
    tweet_period_secs = d.get('tweet_period_secs')
    environ = d.get('environ', {})
    mongo_db_name = d.get('mongo_db_name')
    mongo_articles_col_name = d.get('mongo_articles_col_name')
    return __get_the_real_list(the_list=the_list, logger=logger, ts_tweeted_time=ts_tweeted_time, tweet_period_secs=tweet_period_secs, environ=environ, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name)


def __get_the_real_list(the_list=None, logger=None, ts_tweeted_time=None, tweet_period_secs=None, environ=None, mongo_db_name=None, mongo_articles_col_name=None):
    the_real_list = []
    # _utils.timeStamp(offset=-(1*60*60), use_iso=True)
    for anId in the_list:
        item = __get_articles(_id=anId, environ=environ, mongo_db_name=mongo_db_name,  mongo_articles_col_name=mongo_articles_col_name)
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


def update_the_article(p1={},p2={}):
    '''
    Called from outside this module because there are issues with the way kwargs are being used.
    '''
    d = p1 if (isinstance(p1, dict)) else p2 if (isinstance(p2, dict)) else None
    assert d, 'Missing parameters.'
    item = d.get('item', {})
    the_choice = d.get('the_choice')
    ts_current_time = d.get('ts_current_time')
    logger = d.get('logger')
    environ = d.get('environ', {})
    mongo_db_name = d.get('mongo_db_name')
    mongo_articles_col_name = d.get('mongo_articles_col_name')
    return __update_the_article(item=item, the_choice=the_choice, ts_current_time=ts_current_time, logger=logger, environ=environ, mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name)


def __update_the_article(item=None, the_choice=None, ts_current_time=None, logger=None, environ={}, mongo_db_name=None, mongo_articles_col_name=None):
    assert item, 'Missing item.'
    assert the_choice, 'Missing the_choice.'
    assert ts_current_time, 'Missing ts_current_time.'
    
    the_update = { 'tweeted_time': ts_current_time}

    __rotation__ = '__rotation__'
    bucket = item.get(__rotation__, [])
    bucket.append(ts_current_time)
    the_update[__rotation__] = most_recent_30_days(bucket)

    msg = 'Updating: id: {}, {}'.format(the_choice, the_update)
    print(msg)
    if (logger):
        logger.info(msg)
    resp = __store_article_data(item, update=the_update, environ=environ, mongo_db_name=mongo_db_name,  mongo_articles_col_name=mongo_articles_col_name)
    assert isinstance(resp, int), 'Problem with the response? Expected int value but got {}'.format(resp)
    print('Update was done.')
    
    return the_update[__rotation__]
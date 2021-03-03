import random
from datetime import datetime

from vyperlogix.misc import _utils
from bson.objectid import ObjectId
from vyperlogix.mongo import vyperapi
from vyperlogix.decorators import __with
from vyperlogix.decorators import args

__rotation__ = '__rotation__'
__plans__ = '__plans__'


def __get_the_plan(environ=None, mongo_db_name=None, mongo_articles_col_name=None, criteria=None, callback=None):
    @__with.database(environ=environ)
    def db_get_the_plan(db=None):
        assert vyperapi.is_not_none(db), 'There is no db.'
        assert vyperapi.is_not_none(mongo_db_name), 'There is no mongo_db_name.'
        assert vyperapi.is_not_none(mongo_articles_col_name), 'There is no mongo_articles_col_name.'

        tb_name = mongo_db_name
        col_name = mongo_articles_col_name
        table = db[tb_name]
        coll = table[col_name]

        find_in_collection = lambda c,criteria=criteria:c.find_one() if (not criteria) else c.find_one(criteria)
        doc = find_in_collection(coll, criteria=criteria)
        if (callable(callback)):
            callback(coll=coll, doc=doc)
        return doc
    return db_get_the_plan()


def __store_the_plan(data, environ=None, mongo_db_name=None, mongo_articles_col_name=None, update=None):
    @__with.database(environ=environ)
    def db_store_the_plan(db=None, data=None):
        assert vyperapi.is_not_none(db), 'There is no db.'
        assert vyperapi.is_not_none(mongo_db_name), 'There is no mongo_db_name.'
        assert vyperapi.is_not_none(mongo_articles_col_name), 'There is no mongo_articles_col_name.'

        tb_name = mongo_db_name
        col_name = mongo_articles_col_name
        table = db[tb_name]
        coll = table[col_name]

        count = -1
        if (data):
            _id = data.get('_id')
            if (_id) and (update is not None):
                update['updated_time'] = datetime.utcnow()
                newvalue = { "$set": update }
                coll.update_one({'_id': _id}, newvalue)
        else:
            update['created_time'] = datetime.utcnow()
            coll.insert_one(update)

        count = coll.count_documents({})
        return count
    return db_store_the_plan(data=data)


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


@args.kwargs(__get_articles)
def get_articles(*args, **kwargs):
    pass

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
                if (update is not None):
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



def __get_the_real_list(the_list=None, logger=None, ts_tweeted_time=None, tweet_period_secs=None, environ=None, mongo_db_name=None, mongo_articles_col_name=None):
    the_real_list = []
    for anId in the_list:
        item = __get_articles(_id=anId, environ=environ, mongo_db_name=mongo_db_name,  mongo_articles_col_name=mongo_articles_col_name)
        if (item):
            sz = item.get('friends_link')
            tt = item.get('tweeted_time')
            msg = 'id: {}, sz: {}, tt: {}'.format(anId, sz, tt)
            if (logger):
                logger.info(msg)
            
            if (tt is None):
                the_real_list.append(anId)
                msg = 'Added to the_real_list: {}\n'.format(anId)
                if (logger):
                    logger.info(msg)
                continue
            
            dt_target = datetime.fromisoformat(ts_tweeted_time)
            dt_item = datetime.fromisoformat(tt)
            delta = max(dt_target, dt_item) - min(dt_target, dt_item)
            __is__ = (delta.total_seconds() < tweet_period_secs) or (not item.get(__rotation__))
            msg = 'delta: {}, dt_target: {}, dt_item: {}, delta.total_seconds(): {}, tweet_period_secs: {}, __is__: {}'.format(delta, dt_target, dt_item, delta.total_seconds(), tweet_period_secs, __is__)
            if (logger):
                logger.info(msg)
            
            the_real_list.append({'_id':anId, __rotation__:item.get(__rotation__, []), 'secs': delta.total_seconds(), '__is__': __is__})
            msg = 'Added to the_real_list: {}\n'.format(anId)
            if (logger):
                logger.info(msg)
    return the_real_list


@args.kwargs(__get_the_real_list)
def get_the_real_list(*args, **kwargs):
    pass

def __get_a_choice(the_list=None, ts_current_time=None, logger=None):
    choice = None
    assert isinstance(the_list, list), 'Wheres the list?'
    msg = 'the_list - the_list has {} items.'.format(len(the_list))
    logger.info(msg)
    if (len(the_list) > 0):
        priorities1 = [item for item in the_list if (isinstance(item, str))]
        msg = 'priorities1 has {} items.'.format(len(priorities1))
        logger.info(msg)
        if (len(priorities1) > 0):
            choice = random.choice(priorities1)
            msg = 'priorities1 has choice {}.'.format(choice)
            logger.info(msg)
        else:
            priorities2 = [item for item in the_list if (not isinstance(item, str)) and (not item.get(__rotation__))]
            msg = 'priorities2 has {} items.'.format(len(priorities2))
            logger.info(msg)
            if (len(priorities2) > 0):
                choice = random.choice(priorities2)
                msg = 'priorities2 has choice {}.'.format(choice)
                logger.info(msg)
            else:
                today_ymd = ts_current_time.split('T')[0]+'T' if (ts_current_time is not None) and (ts_current_time.find('T') > -1) else None
                def pick_from_list(l_ts):
                    '''
                    return True or False. True if no times in list for last 24 hours else False.
                    '''
                    for t in l_ts:
                        if (t.find(today_ymd) > -1):
                            return False
                    return True
                
                priorities3 = [item for item in the_list if (not isinstance(item, str)) and (pick_from_list(item.get(__rotation__, [])))]
                msg = 'priorities3 has {} items.'.format(len(priorities3))
                logger.info(msg)
                if (len(priorities3) > 0):
                    priorities3 = sorted(priorities3, key=lambda item: len(item.get(__rotation__, [])), reverse=False)
                    choice = priorities3[0]
                    msg = 'priorities3 has choice {}.'.format(choice)
                    logger.info(msg)
                else:
                    priorities4 = [item for item in the_list if (not isinstance(item, str)) and (not pick_from_list(item.get(__rotation__, [])))]
                    msg = 'priorities4 has {} items.'.format(len(priorities4))
                    logger.info(msg)
                    priorities4 = sorted(priorities4, key=lambda item: len(item.get(__rotation__, [])), reverse=False)
                    choice = priorities4[0]
                    msg = 'priorities4 has choice {}.'.format(choice)
                    logger.info(msg)
    msg = 'choice is  {}.'.format(choice)
    logger.info(msg)
    return choice

@args.kwargs(__get_a_choice)
def get_a_choice(*args, **kwargs):
    pass


def most_recent_30_days(bucket):
    '''
    To Do: Do some analysis to see if there are any articles that have not been tweeted recently? (Whatever thay means.)
    '''
    period_secs = 30*24*60*60
    thirty_days_ago = datetime.fromisoformat(_utils.timeStamp(offset=-period_secs, use_iso=True))
    new_bucket = [] if (isinstance(bucket, list)) else {} if (isinstance(bucket, dict)) else None
    if (new_bucket is not None):
        for ts in bucket if (isinstance(bucket, list)) else bucket.keys() if (isinstance(bucket, dict)) else []:
            dt = datetime.fromisoformat(ts)
            delta = dt - thirty_days_ago
            __is__ = delta.total_seconds() < period_secs
            if (__is__):
                if (isinstance(bucket, list)):
                    new_bucket.append(ts)
                elif (isinstance(bucket, dict)):
                    new_bucket[ts] = bucket.get(ts)
    return new_bucket


def __update_the_article(item=None, the_choice=None, ts_current_time=None, logger=None, environ={}, mongo_db_name=None, mongo_articles_col_name=None):
    assert item, 'Missing item.'
    assert ts_current_time, 'Missing ts_current_time.'
    
    the_update = the_choice
    if (the_choice is not None):
        the_update = { 'tweeted_time': ts_current_time}

        bucket = item.get(__rotation__, [])
        bucket.append(ts_current_time)
        the_update[__rotation__] = most_recent_30_days(bucket)

        msg = 'Updating: id: {}, {}'.format(the_choice, the_update)
        if (logger):
            logger.info(msg)
    resp = __store_article_data(item, update=the_update, environ=environ, mongo_db_name=mongo_db_name,  mongo_articles_col_name=mongo_articles_col_name)
    assert isinstance(resp, int), 'Problem with the response? Expected int value but got {}'.format(resp)
    print('Update was done.')
    
    return the_update.get(__rotation__, []) if (the_choice is not None) else []

@args.kwargs(__update_the_article)
def update_the_article(*args, **kwargs):
    pass


def __update_the_plan(the_plan=None, ts_current_time=None, logger=None, environ={}, mongo_db_name=None, mongo_articles_col_name=None):
    assert the_plan, 'Missing the_plan.'
    assert ts_current_time, 'Missing ts_current_time.'
    
    plan = __get_the_plan(mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, environ=environ)
    plan = plan[0] if (isinstance(plan, list)) else plan
    the_update = { 'updated_time': ts_current_time}

    logger.info('DEBUG: plan -> {}'.format(plan))
    bucket = plan.get(__plans__, {}) if (plan and (not isinstance(plan, str))) else {}
    bucket[ts_current_time] = the_plan
    the_update[__plans__] = most_recent_30_days(bucket)

    msg = 'Updating: id: {}, {}'.format(the_plan, the_update)
    if (logger):
        logger.info(msg)
    resp = __store_the_plan(plan, update=the_update, environ=environ, mongo_db_name=mongo_db_name,  mongo_articles_col_name=mongo_articles_col_name)
    assert isinstance(resp, int), 'Problem with the response? Expected int value but got {}'.format(resp)
    
    return the_update.get(__plans__, [])

@args.kwargs(__update_the_plan)
def update_the_plan(*args, **kwargs):
    pass


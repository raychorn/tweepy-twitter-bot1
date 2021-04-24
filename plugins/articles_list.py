import os
import sys
import random
import traceback
import mujson as json

from datetime import datetime, date

from vyperlogix.iterators.dict import dictutils

from vyperlogix.misc import _utils
from vyperlogix.misc import normalize_int_from_str
from bson.objectid import ObjectId
from vyperlogix.mongo import vyperapi
from vyperlogix.decorators import __with
from vyperlogix.decorators import args

from vyperlogix.hash.dict import SmartDict

find_in_collection = lambda c,criteria:c.find() if (not criteria) else c.find(criteria)

is_really_a_string = lambda s:(s is not None) and (len(s) > 0)

__doy__ = lambda args:date(args[0],args[1],args[2]).timetuple().tm_yday if (len(args) == 3) else None
doy_from_ts = lambda ts:__doy__([int(s) for s in ts.split('T')[0].split('-')])

get_rotations_from = lambda item:item.get(__rotation__, []) if (isinstance(item.get(__rotation__, []), list)) else []

collection_name = lambda c,t:'{}{}{}'.format(c,'+' if (is_really_a_string(t)) else '', t if (is_really_a_string(t)) else '')
database_name = lambda db,t:'{}{}{}'.format(db,'+' if (is_really_a_string(t)) else '', t if (is_really_a_string(t)) else '')
        
class RotationProcessor(dict):
    def __setitem__(self, k, v):
        '''
        key is the timestamp and value is a number > 0
        
        ts -> day_of_year -> key
        
        value is dict where key is the hour number and value is the count for that hour
        '''
        toks = k.split('T')
        yy,mm,dd = tuple([int(s) for s in toks[0].split('-')])
        day_of_year = date(yy,mm,dd).timetuple().tm_yday
        d = self.get(day_of_year, SmartDict())
        d['{}'.format(int(toks[-1].split(':')[0]))] = v
        return super().__setitem__(day_of_year, d)


__rotation__ = '__rotation__'
__plans__ = '__plans__'
__rotation_processor__ = '__rotation_processor__'


def __get_the_plan(environ=None, tenant_id=None, mongo_db_name=None, mongo_articles_col_name=None, criteria=None, callback=None):
    @__with.database(environ=environ)
    def db_get_the_plan(db=None):
        assert vyperapi.is_not_none(db), 'There is no db.'
        assert vyperapi.is_not_none(mongo_db_name), 'There is no mongo_db_name.'
        assert vyperapi.is_not_none(mongo_articles_col_name), 'There is no mongo_articles_col_name.'

        tb_name = mongo_db_name
        col_name = mongo_articles_col_name
        table = db[tb_name]
        coll = table[col_name]
        
        accounts = find_in_collection(coll, criteria={'uuid': tenant_id})
        assert accounts.count() == 1, 'Cannot find the account for tenant #{}.'.format(tenant_id)
        
        account = accounts[0]

        doc = accounts[0].get('__plans__')
        if (callable(callback)):
            callback(coll=coll, doc=doc)
        return doc
    return db_get_the_plan()



def __reset_the_plans(environ=None, twitter_bot_account=None, callback=None, logger=None): # , tenant_id=None, mongo_db_name=None, mongo_articles_col_name=None
    def handle_the_doc(coll=None, doc=None):
        print('DEBUG: (__reset_the_plans.1) {} -> {}'.format(coll, doc))

    assert (twitter_bot_account is not None), 'Missing the twitter_bot_account. Cannot proceed.'
    the_plan = __get_the_plan(mongo_db_name=twitter_bot_account.mongo_db_name, mongo_articles_col_name=twitter_bot_account.mongo_twitterbot_account_col_name, environ=environ, tenant_id=twitter_bot_account.tenant_id, callback=handle_the_doc)

    return the_plan



@args.kwargs(__reset_the_plans)
def reset_article_plans(*args, **kwargs):
    pass



def __store_the_plan(data, environ=None, tenant_id=None, mongo_db_name=None, mongo_articles_col_name=None, update=None):
    @__with.database(environ=environ)
    def db_store_the_plan(db=None, data=None):
        assert vyperapi.is_not_none(db), 'There is no db.'
        assert vyperapi.is_not_none(mongo_db_name), 'There is no mongo_db_name.'
        assert vyperapi.is_not_none(mongo_articles_col_name), 'There is no mongo_articles_col_name.'

        tb_name = mongo_db_name
        col_name = mongo_articles_col_name
        table = db[tb_name]
        coll = table[col_name]

        accounts = find_in_collection(coll, criteria={'uuid': tenant_id})
        assert accounts.count() == 1, 'Cannot find the account for tenant #{}.'.format(tenant_id)
        
        account = accounts[0]

        doc = accounts[0].get('__plans__')
        _id = accounts[0].get('_id')
        
        count = -1
        if (data):
            if (_id) and (update is not None):
                update['updated_time'] = datetime.utcnow()
                newvalue = { "$set": update }
                coll.update_one({'_id': _id}, newvalue)
        else:
            update['created_time'] = datetime.utcnow()
            newvalue = { "$set": update }
            coll.update_one({'_id': _id}, newvalue)

        count = accounts.count()
        return count
    return db_store_the_plan(data=data)


def __get_articles(_id=None, environ=None, tenant_id=None, mongo_db_name=None, mongo_articles_col_name=None, criteria=None, callback=None, logger=None):
    @__with.database(environ=environ)
    def db_get_articles(db=None, _id=None):
        mongo_db_name = environ.get('mongo_db_name')
        mongo_articles_col_name = environ.get('mongo_articles_col_name')
        assert vyperapi.is_not_none(db), 'There is no db.'
        assert vyperapi.is_not_none(mongo_db_name), 'There is no mongo_db_name.'
        assert vyperapi.is_not_none(mongo_articles_col_name), 'There is no mongo_articles_col_name.'

        tb_name = mongo_db_name
        col_name = mongo_articles_col_name
        table = db[database_name(tb_name, tenant_id)]
        coll = table[col_name]

        recs = []
        print('DEBUG: logger -> {}'.format(logger))
        if (logger):
            logger.info('DEBUG: (1) _id -> {}'.format(_id))
        _id = _id[0] if (isinstance(_id, tuple)) else _id
        if (logger):
            logger.info('DEBUG: (2) _id -> {}'.format(_id))
        if (not _id) or (_id == tuple([])):
            if (logger):
                logger.info('DEBUG: (3) criteria -> {}'.format(criteria))
            try:
                recs = [str(doc.get('_id')) for doc in find_in_collection(coll, criteria=criteria)]
            except Exception as ex:
                extype, ex, tb = sys.exc_info()
                for l in traceback.format_exception(extype, ex, tb):
                    if (logger):
                        logger.error(l.rstrip())
                recs = []
        else:
            if (logger):
                logger.info('DEBUG: (4) _id -> {}'.format(_id))
            recs = coll.find_one({"_id": ObjectId(_id)})
        if (callable(callback)):
            callback(coll=coll, recs=recs, _id=_id)
        return recs
    return db_get_articles(_id=_id)


@args.kwargs(__get_articles)
def get_articles(*args, **kwargs):
    pass


def __store_article_data(data, environ=None, tenant_id=None, mongo_db_name=None, mongo_articles_col_name=None, update=None):
    @__with.database(environ=environ)
    def db_store_article_data(db=None, data=None):
        mongo_db_name = environ.get('mongo_db_name')
        mongo_articles_col_name = environ.get('mongo_articles_col_name')
        assert vyperapi.is_not_none(db), 'There is no db.'
        assert vyperapi.is_not_none(mongo_db_name), 'There is no mongo_db_name.'
        assert vyperapi.is_not_none(mongo_articles_col_name), 'There is no mongo_articles_col_name.'

        tb_name = mongo_db_name
        col_name = mongo_articles_col_name
        table = db[database_name(tb_name, tenant_id)]
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



def __get_the_real_list(the_list=None, ts_tweeted_time=None, tweet_period_secs=None, environ=None, mongo_db_name=None, mongo_articles_col_name=None, logger=None):
    the_real_list = []
    for anId in the_list:
        if (logger):
            logger.info('DEBUG: (***) anId -> {}'.format(anId))
        item = __get_articles(_id=anId, environ=environ, mongo_db_name=mongo_db_name,  mongo_articles_col_name=mongo_articles_col_name, logger=logger)
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
            __is__ = (delta.total_seconds() < tweet_period_secs) or (get_rotations_from(item) is not None)
            msg = 'delta: {}, dt_target: {}, dt_item: {}, delta.total_seconds(): {}, tweet_period_secs: {}, __is__: {}'.format(delta, dt_target, dt_item, delta.total_seconds(), tweet_period_secs, __is__)
            if (logger):
                logger.info(msg)
            
            the_real_list.append({'_id':anId, __rotation__:get_rotations_from(item), 'secs': delta.total_seconds(), '__is__': __is__})
            msg = 'Added to the_real_list: {}\n'.format(anId)
            if (logger):
                logger.info(msg)
    return the_real_list


@args.kwargs(__get_the_real_list)
def get_the_real_list(*args, **kwargs):
    pass

def __get_a_choice(the_list=None, ts_current_time=None, this_process={}, environ=None, tenant_id=None, mongo_db_name=None, mongo_articles_col_name=None, logger=None):
    choice = None
    the_process = []
    assert isinstance(the_list, list), 'Wheres the list?'
    msg = 'the_list - the_list has {} items.'.format(len(the_list))
    assert isinstance(ts_current_time, str), 'Missing a usable ts_current_time.'
    assert isinstance(this_process, dict), 'Missing a usable this_process.'
    assert environ is not None, 'Missing the environ.'
    assert isinstance(mongo_db_name, str), 'Missing the mongo_db_name.'
    assert isinstance(mongo_articles_col_name, str), 'Missing the mongo_articles_col_name.'
    logger.info(msg)
    if (len(the_list) > 0):
        priorities1 = [item for item in the_list if (isinstance(item, str))]
        msg = 'priorities1 has {} items.'.format(len(priorities1))
        logger.info(msg)
        the_process.append('1={}'.format(len(priorities1)))
        if (len(priorities1) > 0):
            choice = random.choice(priorities1)
            msg = 'priorities1 has choice {}.'.format(choice)
            logger.info(msg)
        else:
            the_plan = __get_the_plan(mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, environ=environ, tenant_id=tenant_id)

            if (the_plan):
                doy = '{}'.format(doy_from_ts(ts_current_time))
                def has_rotations_now(obj, p=None):
                    if (p is not None):
                        plans = p.get('__plans__', {})
                        if (isinstance(plans, dict)):
                            specific = plans.get(obj.get('_id'), {})
                            if (isinstance(specific, dict)):
                                process = specific.get('__the_rotation__', {})
                                if (not isinstance(process, dict)):
                                    process = {}
                                if (isinstance(process, dict)):
                                    rotations = process.get(doy, {})
                                    if (isinstance(rotations, dict)):
                                        return len(rotations) > 0
                    return False
                priorities2 = [item for item in the_list if (not isinstance(item, str)) and (not has_rotations_now(item, p=the_plan))]
            else:
                priorities2 = [item for item in the_list if (not isinstance(item, str))]
            msg = 'priorities2 has {} items.'.format(len(priorities2))
            logger.info(msg)
            the_process.append('2={}'.format(len(priorities2)))
            if (len(priorities2) > 0):
                choice = random.choice(priorities2)
                msg = 'priorities2 has choice {}.'.format(choice)
                logger.info(msg)
    msg = 'choice is  {}.'.format(choice)
    logger.info(msg)
    the_process.append(choice)
    this_process[ts_current_time] = the_process
    return choice

@args.kwargs(__get_a_choice)
def get_a_choice(*args, **kwargs):
    pass

def __reset_plans_for_choices(the_list=None, ts_current_time=None, environ=None, tenant_id=None, mongo_db_name=None, mongo_articles_col_name=None, logger=None):
    choice = None
    assert isinstance(the_list, list), 'Wheres the list?'
    msg = 'the_list - the_list has {} items.'.format(len(the_list))
    assert isinstance(ts_current_time, str), 'Missing a usable ts_current_time.'
    assert environ is not None, 'Missing the environ.'
    assert isinstance(mongo_db_name, str), 'Missing the mongo_db_name.'
    assert isinstance(mongo_articles_col_name, str), 'Missing the mongo_articles_col_name.'
    logger.info(msg)
    if (len(the_list) > 0):
        the_plan = __get_the_plan(mongo_db_name=mongo_db_name, mongo_articles_col_name=mongo_articles_col_name, environ=environ, tenant_id=tenant_id)
        if (the_plan):
            doy = '{}'.format(doy_from_ts(ts_current_time))
            def has_rotations_now(obj, p=None, reset=False):
                if (p is not None):
                    plans = p.get('__plans__', {})
                    if (isinstance(plans, dict)):
                        specific = plans.get(obj.get('_id'), {})
                        if (isinstance(specific, dict)):
                            process = specific.get('__the_rotation__', {})
                            if (isinstance(process, dict)):
                                if (reset):
                                    process[doy] = {}
                                else:
                                    rotations = process.get(doy, {})
                                    if (isinstance(rotations, dict)):
                                        return len(rotations) > 0
                return False
            choices = [item for item in the_list if (not isinstance(item, str)) and (not has_rotations_now(item, p=the_plan))]
            if (len(choices) == 0):
                for item in the_list:
                    if (not isinstance(item, str)):
                        has_rotations_now(item, p=the_plan, reset=True)
                resp = __store_the_plan(the_plan, update=the_plan, environ=environ, tenant_id=tenant_id, mongo_db_name=mongo_db_name,  mongo_articles_col_name=mongo_articles_col_name)
                assert isinstance(resp, int), 'Problem with the response? Expected int value but got {}'.format(resp)
    return choice

@args.kwargs(__reset_plans_for_choices)
def reset_plans_for_choices(*args, **kwargs):
    pass


def most_recent_number_of_days(bucket, num_days=30):
    '''
    To Do: Do some analysis to see if there are any articles that have not been tweeted recently? (Whatever thay means.)
    '''
    period_secs = (normalize_int_from_str(num_days)*24*60*60)
    thirty_days_ago = datetime.fromisoformat(_utils.timeStamp(offset=-period_secs, use_iso=True))
    period_secs += 3600  # Daylight Savings Time issue? Or typical translation bias?
    new_bucket = [] if (isinstance(bucket, list)) else {} if (isinstance(bucket, dict)) else None
    if (new_bucket is not None):
        for ts in bucket if (isinstance(bucket, list)) else bucket.keys() if (isinstance(bucket, dict)) else []:
            if (len(ts.split('T')) > 1):
                dt = datetime.fromisoformat(ts)
                delta = dt - thirty_days_ago
                __is__ = delta.total_seconds() < period_secs
                if (__is__):
                    if (isinstance(bucket, list)):
                        new_bucket.append(ts)
                    elif (isinstance(bucket, dict)):
                        new_bucket[ts] = bucket.get(ts)
            else:
                new_bucket[ts] = bucket.get(ts)
    assert len(new_bucket) > 0, 'There cannot be less than one item after an update.'
    return new_bucket


def __update_the_article(item=None, the_choice=None, tenant_id=None, ts_current_time=None, logger=None, environ={}, mongo_db_name=None, mongo_articles_col_name=None):
    '''
    deprecated. The rotations are now stored on the Account and not the Article(s). 04-15-2021
    '''
    assert item, 'Missing item.'

    the_update = the_choice
    if (the_choice is not None):
        the_update = {}

        if (is_really_a_string(ts_current_time)):
            the_update = { 'tweeted_time': ts_current_time}

            bucket = get_rotations_from(item)
            bucket.append(ts_current_time)
            the_update[__rotation__] = most_recent_number_of_days(bucket, num_days=normalize_int_from_str(os.environ.get('max_days_in_rotations', 5)))
        
            doy = '{}'.format(doy_from_ts(ts_current_time))
            
            the_processor = RotationProcessor(item.get(__rotation_processor__, {}))
            retirees = []
            for __item in the_update[__rotation__]:
                if (len(__item.split('T')) > 1):
                    the_processor[__item] = 1
                    retirees.append(__item)
            for r in retirees:
                i = the_update[__rotation__].index(r)
                del the_update[__rotation__][i]
            the_update[__rotation_processor__] = the_processor

        msg = 'Updating: id: {}, {}'.format(the_choice, the_update)
        if (logger):
            logger.info(msg)
    the_update = dictutils.bson_cleaner(the_update, returns_json=False)
    resp = __store_article_data(item, update=the_update, tenant_id=tenant_id, environ=environ, mongo_db_name=mongo_db_name,  mongo_articles_col_name=mongo_articles_col_name)
    assert isinstance(resp, int), 'Problem with the response? Expected int value but got {}'.format(resp)
    print('Update was done.')
    
    return the_update.get(__rotation_processor__, []) if (the_choice is not None) else []

@args.kwargs(__update_the_article)
def update_the_article(*args, **kwargs):
    pass


def __update_the_plan(the_plan=None, ts_current_time=None, the_choice=None, logger=None, environ={}, twitter_bot_account=None):
    assert the_plan, 'Missing the_plan.'
    assert ts_current_time, 'Missing ts_current_time.'

    #the_plan = __get_the_plan(mongo_db_name=twitter_bot_account.mongo_db_name, mongo_articles_col_name=twitter_bot_account.mongo_twitterbot_account_col_name, environ=environ, tenant_id=twitter_bot_account.tenant_id, callback=handle_the_doc)

    
    plan = __get_the_plan(mongo_db_name=twitter_bot_account.mongo_db_name, mongo_articles_col_name=twitter_bot_account.mongo_twitterbot_account_col_name, environ=environ, tenant_id=twitter_bot_account.tenant_id)
    plan = plan[0] if (isinstance(plan, list) and (len(plan) > 0)) else plan
    the_update = { 'updated_time': ts_current_time}

    bucket = plan.get(__plans__, {}) if (plan and (not isinstance(plan, str))) else {}
    bucket[the_choice.get('_id') if (not isinstance(the_choice, str)) else the_choice] = the_plan
    if (1):
        the_update[__plans__] = bucket
        resp = __store_the_plan(plan, update=the_update, environ=environ, tenant_id=twitter_bot_account.tenant_id, mongo_db_name=twitter_bot_account.mongo_db_name,  mongo_articles_col_name=twitter_bot_account.mongo_twitterbot_account_col_name)
        assert isinstance(resp, int), 'Problem with the response? Expected int value but got {}'.format(resp)

    return the_update.get(__plans__, [])

@args.kwargs(__update_the_plan)
def update_the_plan(*args, **kwargs):
    pass


#######################################################################
#######################################################################



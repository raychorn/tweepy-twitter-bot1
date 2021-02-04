import random
from datetime import datetime

from vyperlogix.misc import _utils
from bson.objectid import ObjectId
from vyperlogix.mongo import vyperapi
from vyperlogix.decorators import __with
from vyperlogix.decorators import args



def __store_hashtag(data, environ=None):
    @__with.database(environ=environ)
    def db_store_hashtag(db=None, data=None):
        mongo_db_name = environ.get('mongo_db_name')
        mongo_hashtags_col_name = environ.get('mongo_hashtags_col_name')
        assert vyperapi.is_not_none(db), 'There is no db.'
        assert vyperapi.is_not_none(mongo_db_name), 'There is no mongo_db_name.'
        assert vyperapi.is_not_none(mongo_hashtags_col_name), 'There is no mongo_hashtags_col_name.'

        tb_name = mongo_db_name
        col_name = mongo_hashtags_col_name
        table = db[tb_name]
        coll = table[col_name]

        count = -1
        hashtag = data.get('hashtag')
        if ((hashtag) and (len(hashtag) > 0)):
            doc = coll.find_one({ "hashtag": hashtag })
            if (doc):
                data['updated_time'] = datetime.utcnow()
                newvalue = { "$set": data }
                coll.update_one({'_id': doc.get('_id')}, newvalue)
            else:
                data['created_time'] = datetime.utcnow()
                coll.insert_one(data)

            count = coll.count_documents({})
        return count
    return db_store_hashtag(data=data)


@args.kwargs(__store_hashtag)
def store_one_hashtag(*args, **kwargs):
    pass


def __get_hashtag_matching(hashtag=None, environ=None, criteria=None, logger=None):
    @__with.database(environ=environ)
    def db_get_hashtag_matching(db=None, hashtag=None):
        mongo_db_name = environ.get('mongo_db_name')
        mongo_hashtags_col_name = environ.get('mongo_hashtags_col_name')
        assert vyperapi.is_not_none(db), 'There is no db.'
        assert vyperapi.is_not_none(mongo_db_name), 'There is no mongo_db_name.'
        assert vyperapi.is_not_none(mongo_hashtags_col_name), 'There is no mongo_hashtags_col_name.'

        tb_name = mongo_db_name
        col_name = mongo_hashtags_col_name
        table = db[tb_name]
        coll = table[col_name]

        docs = None
        if ((hashtag) and (len(hashtag) > 0)):
            if (not criteria):
                docs = coll.find_one({ "hashtag": hashtag })
            elif (criteria):
                find_in_collection = lambda c,criteria=criteria:c.find_one({ "hashtag": hashtag }) if (not criteria) else c.find_one(criteria)
                docs = find_in_collection(coll, criteria=criteria)
        elif (criteria):
            find_in_collection = lambda c,criteria=criteria:c.find_one({ "hashtag": hashtag }) if (not criteria) else c.find_one(criteria)
            docs = find_in_collection(coll, criteria=criteria)
        return docs
    return db_get_hashtag_matching(hashtag=hashtag)


@args.kwargs(__get_hashtag_matching)
def get_hashtag_matching(*args, **kwargs):
    pass


def __delete_all_hashtags(environ=None, logger=None):
    @__with.database(environ=environ)
    def db_delete_all_hashtags(db=None, hashtag=None):
        mongo_db_name = environ.get('mongo_db_name')
        mongo_hashtags_col_name = environ.get('mongo_hashtags_col_name')
        assert vyperapi.is_not_none(db), 'There is no db.'
        assert vyperapi.is_not_none(mongo_db_name), 'There is no mongo_db_name.'
        assert vyperapi.is_not_none(mongo_hashtags_col_name), 'There is no mongo_hashtags_col_name.'

        tb_name = mongo_db_name
        col_name = mongo_hashtags_col_name
        table = db[tb_name]
        coll = table[col_name]

        coll.delete_many({})
        count = coll.count_documents({})
        return count
    return db_delete_all_hashtags()


@args.kwargs(__delete_all_hashtags)
def delete_all_hashtags(*args, **kwargs):
    pass


def __get_final_word_cloud(environ=None, callback=None, logger=None):
    @__with.database(environ=environ)
    def db_get_final_word_cloud(db=None, _id=None):
        mongo_db_name = environ.get('mongo_db_name')
        mongo_cloud_col_name = environ.get('mongo_cloud_col_name')
        assert vyperapi.is_not_none(db), 'There is no db.'
        assert vyperapi.is_not_none(mongo_db_name), 'There is no mongo_db_name.'
        assert vyperapi.is_not_none(mongo_cloud_col_name), 'There is no mongo_cloud_col_name.'

        tb_name = mongo_db_name
        col_name = mongo_cloud_col_name
        table = db[tb_name]
        coll = table[col_name]

        doc = coll.find_one()
        if (callable(callback)):
            callback(coll=coll, doc=doc)
        return doc
    return db_get_final_word_cloud()


@args.kwargs(__get_final_word_cloud)
def get_final_word_cloud(*args, **kwargs):
    pass


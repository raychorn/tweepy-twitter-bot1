from datetime import datetime

from vyperlogix.misc import _utils
from bson.objectid import ObjectId
from vyperlogix.mongo import vyperapi
from vyperlogix.decorators import __with
from vyperlogix.decorators import args


def __store_the_account(data, environ=None, tenant_id=None, mongo_db_name=None, mongo_col_name=None, update=None):
    @__with.database(environ=environ)
    def db_store_the_account(db=None, data=None):
        assert vyperapi.is_not_none(db), 'There is no db.'
        assert vyperapi.is_not_none(mongo_db_name), 'There is no mongo_db_name.'
        assert vyperapi.is_not_none(mongo_col_name), 'There is no mongo_col_name.'

        tb_name = mongo_db_name
        col_name = mongo_col_name
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
    return db_store_the_account(data=data)


def __get_account_id(environ=None, tenant_id=None, mongo_db_name=None, mongo_col_name=None, criteria=None, callback=None, logger=None):
    @__with.database(environ=environ)
    def db_get_account_id(db=None, data=None):
        assert vyperapi.is_not_none(db), 'There is no db.'
        assert vyperapi.is_not_none(mongo_db_name), 'There is no mongo_db_name.'
        assert vyperapi.is_not_none(mongo_col_name), 'There is no mongo_col_name.'

        tb_name = mongo_db_name
        col_name = mongo_col_name
        table = db[tb_name]
        coll = table[col_name]

        __data__ = {'uuid': tenant_id}
        find_in_collection = lambda c,criteria=criteria:c.find_one() if (not criteria) else c.find_one(criteria)
        doc = find_in_collection(coll, criteria=__data__)
        if (callable(callback)):
            callback(coll=coll, doc=doc)
        elif (doc is None):
            cnt = __store_the_account(__data__, environ=environ, tenant_id=tenant_id, mongo_db_name=mongo_db_name, mongo_col_name=mongo_col_name)
        return doc
    return db_get_account_id()


@args.kwargs(__get_account_id)
def get_account_id(*args, **kwargs):
    pass


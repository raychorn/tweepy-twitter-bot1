from datetime import datetime

from vyperlogix.misc import _utils
from bson.objectid import ObjectId
from vyperlogix.mongo import vyperapi
from vyperlogix.decorators import __with
from vyperlogix.decorators import args



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

        find_in_collection = lambda c,criteria=criteria:c.find_one() if (not criteria) else c.find_one(criteria)
        doc = find_in_collection(coll, criteria={'uuid': tenant_id})
        if (callable(callback)):
            callback(coll=coll, doc=doc)
        return doc
    return db_get_account_id()


@args.kwargs(__get_account_id)
def get_account_id(*args, **kwargs):
    pass


import io
import sys
import traceback

def crud_store_data(environ=None, mongo_db_name=None, mongo_col_name=None, mongo_key_name=None, data=None, criteria=None, uniques=True, using_clean_data=False, verbose=False, debug=False, logger=None):
    '''
    CRUD automation - stores data
    '''
    from vyperlogix.mongo import vyperapi
    from vyperlogix.decorators import __with

    response = {}
    
    assert isinstance(mongo_db_name, str) and (len(mongo_db_name) > 0), '(1) Cannot proceed without a mongo_db_name and "{}" is not usable.'.format(mongo_db_name)
    assert isinstance(mongo_col_name, str) and (len(mongo_col_name) > 0), '(1) Cannot proceed without a mongo_col_name and "{}" is not usable.'.format(mongo_col_name)
    assert (data), '(1) Cannot proceed without data and "{}" is not usable.'.format(data)
    
    def handle_response(data):
        pass

    @__with.mongodb(environ=environ, table_name=mongo_db_name, col_name=mongo_col_name, keyName=mongo_key_name, data=data, criteria=criteria, callback=handle_response, uniques=uniques, using_clean_data=using_clean_data, verbose=verbose, logger=logger)
    def __store_data(db=None, resp=None):
        '''
        The function name must bear the name of "store_data" however it could also be something like "sample_store_data".
        '''
        assert vyperapi.is_not_none(resp), 'There is no data.'
        return resp
    
    __response = __store_data()

    response['response'] = __response

    return response


def crud_get_data(environ=None, mongo_db_name=None, mongo_col_name=None, mongo_key_name=None, criteria=None, verbose=False, debug=False, logger=None):
    '''
    CRUD automation - stores data
    '''
    from vyperlogix.mongo import vyperapi
    from vyperlogix.decorators import __with

    response = {}
    
    assert isinstance(mongo_db_name, str) and (len(mongo_db_name) > 0), '(1) Cannot proceed without a mongo_db_name and "{}" is not usable.'.format(mongo_db_name)
    assert isinstance(mongo_col_name, str) and (len(mongo_col_name) > 0), '(1) Cannot proceed without a mongo_col_name and "{}" is not usable.'.format(mongo_col_name)
    
    @__with.mongodb(environ=environ, table_name=mongo_db_name, col_name=mongo_col_name, criteria=criteria, verbose=debug, logger=logger)
    def __get_data(db=None, resp=None):
        '''
        The function name must bear the name of "store_data" however it could also be something like "sample_store_data".
        '''
        assert vyperapi.is_not_none(resp), 'There is no data.'
        return resp
    
    __response = __get_data()

    response['response'] = __response

    return response


def crud_get_collection(environ=None, mongo_db_name=None, mongo_col_name=None, criteria=None, callback=None, verbose=False, debug=False, logger=None):
    '''
    CRUD automation - performs collection operations
    '''
    from vyperlogix.mongo import vyperapi
    from vyperlogix.decorators import __with

    response = {}
    
    assert isinstance(mongo_db_name, str) and (len(mongo_db_name) > 0), '(1) Cannot proceed without a mongo_db_name and "{}" is not usable.'.format(mongo_db_name)
    assert isinstance(mongo_col_name, str) and (len(mongo_col_name) > 0), '(1) Cannot proceed without a mongo_col_name and "{}" is not usable.'.format(mongo_col_name)
    
    @__with.mongodb(environ=environ, table_name=mongo_db_name, col_name=mongo_col_name, criteria=criteria, callback=callback, verbose=debug, logger=logger)
    def __get_collection(db=None, resp=None):
        '''
        The function name must bear the name of "collection" however it could also be something like "do_something_with_collection".
        '''
        assert vyperapi.is_not_none(resp), 'There is no data.'
        return resp
    
    __response = __get_collection()

    response['response'] = __response

    return response


def crud_delete_data(environ=None, mongo_db_name=None, mongo_col_name=None, mongo_key_name=None, data=None, criteria=None, verbose=False, debug=False, logger=None):
    '''
    CRUD automation - stores data
    '''
    from vyperlogix.mongo import vyperapi
    from vyperlogix.decorators import __with

    response = {}
    
    assert isinstance(mongo_db_name, str) and (len(mongo_db_name) > 0), '(1) Cannot proceed without a mongo_db_name and "{}" is not usable.'.format(mongo_db_name)
    assert isinstance(mongo_col_name, str) and (len(mongo_col_name) > 0), '(1) Cannot proceed without a mongo_col_name and "{}" is not usable.'.format(mongo_col_name)
    assert (isinstance(mongo_key_name, str) and (len(mongo_key_name) > 0)) or (criteria), '(1) Cannot proceed without a mongo_key_name ("{}") or criteria ("{}") and one of these is not usable.'.format(mongo_key_name, criteria)
    assert (data), '(1) Cannot proceed without data and "{}" is not usable.'.format(data)
    
    @__with.mongodb(environ=environ, table_name=mongo_db_name, col_name=mongo_col_name, data=data, criteria=criteria, verbose=debug, logger=logger)
    def __delete_data(db=None, resp=None):
        '''
        The function name must bear the name of "delete_data" however it could also be something like "sample_delete_data".
        '''
        assert vyperapi.is_not_none(resp), 'There is no data.'
        return resp

    __response = __delete_data()

    response['response'] = __response

    return response


def crud_update_data(environ=None, mongo_db_name=None, mongo_col_name=None, mongo_key_name=None, data=None, criteria=None, verbose=False, debug=False, logger=None):
    '''
    CRUD automation - stores data
    '''
    from vyperlogix.mongo import vyperapi
    from vyperlogix.decorators import __with

    response = {}
    
    assert isinstance(mongo_db_name, str) and (len(mongo_db_name) > 0), '(1) Cannot proceed without a mongo_db_name and "{}" is not usable.'.format(mongo_db_name)
    assert isinstance(mongo_col_name, str) and (len(mongo_col_name) > 0), '(1) Cannot proceed without a mongo_col_name and "{}" is not usable.'.format(mongo_col_name)
    assert (isinstance(mongo_key_name, str) and (len(mongo_key_name) > 0)) or (criteria), '(1) Cannot proceed without a mongo_key_name ("{}") or criteria ("{}") and one of these is not usable.'.format(mongo_key_name, criteria)
    assert (data), '(1) Cannot proceed without data and "{}" is not usable.'.format(data)
    
    @__with.mongodb(environ=environ, table_name=mongo_db_name, col_name=mongo_col_name, data=data, criteria=criteria, verbose=debug, logger=logger)
    def __update_data(db=None, resp=None):
        '''
        The function name must bear the name of "delete_data" however it could also be something like "sample_delete_data".
        '''
        assert vyperapi.is_not_none(resp), 'There is no data.'
        return resp

    __response = __update_data()

    response['response'] = __response

    return response


def db_do_with_client(environ=None, source_code=None, verbose=False, debug=False, logger=None):
    '''
    CRUD automation - does stuff with the database client.
    '''
    from vyperlogix.mongo import vyperapi
    from vyperlogix.decorators import __with

    response = {}
    
    @__with.mongodb(environ=environ, verbose=debug, logger=logger)
    def __get_client(resp=None, db=None):
        '''
        Nothing special about this.  All wrapped functions get the db client.
        '''
        assert vyperapi.is_not_none(db), 'There is no db client.'
        return db

    client = __get_client()

    try:
        resp = eval(source_code.format('client')) if (isinstance(source_code, str)) and (source_code.find('{}') > -1) else client
    except:
        e = []
        extype, ex, tb = sys.exc_info()
        for l in traceback.format_exception(extype, ex, tb):
            e.append(l.rstrip())
        fOut = io.StringIO()
        print('EXCEPTION: {}'.format('\n'.join(e)), file=fOut)
        resp = fOut.getvalue()

    response['client'] = resp

    return response



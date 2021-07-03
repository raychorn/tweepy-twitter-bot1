import sys
from uuid import uuid4

from vyperlogix import misc
from vyperlogix.misc import _utils
from vyperlogix.classes.MagicObject import Wrapper

class SmartWrapper(Wrapper):
    __cache__ = {}
    def __init__(self,__object__,callback=None):
        self.__id__ = str(uuid4())
        SmartWrapper.__cache__[self.__id__] = __object__
        self.__callback__ = callback
        self.__stack__ = []
        super().__init__(self)

    def __getattr__(self,name,*args,**kwargs):
        self.__reset_magic__()
        if (name not in ['__iter__']):
            self.__stack__.append(name)
        return super().__getattr__(self,name)
    
    def __setitem__(self,name,value):
        return self.__object__.set(name,value)
    
    def __getitem__(self,name):
        value = self.__object__.get(name)
        if (callable(self.__callback__)):
            try:
                value = self.__callback__(value)
            except:
                pass
        return value
    
    def __call__(self,*args,**kwargs):
        results = None
        n = self.n[0] if (misc.isList(self.n) and (len(self.n) > 0)) else self.n
        if (len(self.__stack__) > 0):
            n = self.__stack__.pop()
            #obj = SmartWrapper.__cache__.get(self.__id__)
        obj = SmartWrapper.__cache__.get(self.__id__)
        if (obj):
            try:
                f = getattr(obj, n)
                results = f(*args,**kwargs)
            except Exception as details:
                results = None
                sys.stderr.write(_utils.formattedException(details=details)+'\n')
        return results


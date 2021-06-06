import os, sys
from dotenv import find_dotenv

def __escape(v):
    from urllib import parse
    return parse.quote_plus(v)

try:
    from vyperlogix.env.environ import MyDotEnv
except ImportError:
    pylib = '/home/raychorn/projects/python-projects/private_vyperlogix_lib3'
    if (not any([f == pylib for f in sys.path])):
        sys.path.insert(0, pylib)
    from vyperlogix.env.environ import MyDotEnv

def get_local_ether_interface():
    import ifcfg
    import ipaddress

    for name, interface in ifcfg.interfaces().items():
        ip_addr = interface.get('inet')
        ip_ether = interface.get('ether')
        if (ip_addr and ip_ether):
            i = ipaddress.ip_address(ip_addr)
            if (i.is_private):
                return interface
    return None
        
local_ether_interface = get_local_ether_interface()
assert local_ether_interface is not None, 'Cannot get the local ip address from the ifconfig interface. Please fix.'
os.environ['LOCAL_INET'] = local_ether_interface.get('inet')

__env__ = {}
env_literals = []
def get_environ_keys(*args, **kwargs):
    from expandvars import expandvars
    
    k = kwargs.get('key')
    v = kwargs.get('value')
    assert (k is not None) and (v is not None), 'Problem with kwargs -> {}, k={}, v={}'.format(kwargs,k,v)
    __logger__ = kwargs.get('logger')
    if (k == '__LITERALS__'):
        for item in v:
            env_literals.append(item)
    if (isinstance(v, str)):
        v = expandvars(v) if (k not in env_literals) else v
        v = __escape(v) if (k in __env__.get('__ESCAPED__', [])) else v
    ignoring = __env__.get('IGNORING', [])
    environ = kwargs.get('environ', None)
    if (isinstance(environ, dict)):
        environ[k] = v
    if (k not in ignoring):
        __env__[k] = v
    if (__logger__):
        __logger__.info('\t{} -> {}'.format(k, environ.get(k)))
    return tuple([k,v])

fp = find_dotenv()
if (fp.find('/docker/')):
    fp = fp.replace('/docker', '')
dotenv = MyDotEnv(fp, verbose=True, interpolate=True, override=True, logger=None, callback=get_environ_keys)
dotenv.set_as_environment_variables()

ignore_values = [
    '/home/raychorn/projects/python-projects/private_vyperlogix_lib3', 
    'COSMOS_INITDB_ROOT_PASSWORD',
    'MONGO_INITDB_ROOT_PASSWORD',
    'COSMOS_URI',
    '__env4__'
]

for k,v in __env__.items():
    try:
        if (isinstance(v, str)) and (not any([v.find(s) > -1 for s in ignore_values])):
            print('{}={}'.format(k,v))
    except:
        pass

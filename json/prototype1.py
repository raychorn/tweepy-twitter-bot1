import os
import sys
import mujson as json

from datetime import datetime, date

try:
    from vyperlogix.misc import _utils
except ImportError:
    pylib = '/home/raychorn/projects/python-projects/private_vyperlogix_lib3'
    if (not any([f == pylib for f in sys.path])):
        print('Adding {}'.format(pylib))
        sys.path.insert(0, pylib)

from vyperlogix.hash.dict import SmartDict

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
        d[int(toks[-1].split(':')[0])] = v
        return super().__setitem__(day_of_year, d)


if (__name__ == '__main__'):
    fpath = os.sep.join([os.path.dirname(sys.argv[0]), "the_update.json"])
    with open(fpath, 'r') as file:
        print('Reading...')
        the_update = json.load(file)
        print('Done Reading!')
        
    processor = RotationProcessor()
        
    for ts,aPlan in the_update.get('__plans__', {}).items():
        for rot in aPlan.get('__the_rotation__', []):
            processor[rot] = 1
        print()

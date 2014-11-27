#!/usr/bin/env python

import pymongo, yaml
from gflags import *

class mongodb(object):
    def __init__(self,configure):
        self.configure = configure

    def connect(self,params):
        self.conn = pymongo.Connection(host=params['host'], port=params['port'])
        self.dbh = self.conn[params['db']]
        assert self.dbh.connection == self.conn
        return self.dbh

    def get(self,condition):
	    pass

    def set(self,records):
	    pass

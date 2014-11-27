#!/usr/bin/env python

import redis

class redis():
	def __init__(self,configure):
		self.configure = configure
	
	def connect(self,params):
		self.POOL = redis.ConnectionPool(host=params['host'],port=params['port'],db=params['db'])
		return self.POOL

	def get(self,name):
		conn = redis.Redis(connect_pool=POOL)
		return conn.get(name)

	def set(self,name,value):
		conn = redis.Redis(connect_pool=POOL)
		return conn.set(name,value)

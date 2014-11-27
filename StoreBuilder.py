#!/usr/bin/env python

from storage.mongodb import mongodb
from storage.redis import redis
# from storage.mysql import mysql
import time

class StoreBuilder(object):

    def __init__(self,configure):
        self.configure = configure

    def create(self,params):
        mongo = mongodb(self.configure)
        self.dbh = mongo.connect(params)
        return self.dbh

    def create_storage(self,store_rules,rule_name):
        store_params = self.get_store_rule(store_rules,rule_name)
        builder_params = self.get_storage(store_params)
        mongo = mongodb(self.configure)
        self.dbh = mongo.connect(builder_params)
        return self.dbh

    def store_url(self,item_name,urls):
        for url_item in urls:
            if url_item!=None:
                query = {"url":url_item}
                urls = {"item":item_name,"url":url_item,"crawl_time":time.time()}
                self.dbh.urls.update(query,urls,upsert=True)

    def get_store_rule(self,store_rules,rule_name):
        store_params = {}
        for store_rule in store_rules:
            if store_rule['name'] == rule_name:
                store_params = store_rule
                break
        return store_params


    def get_storage(self,store_params):
        params = {}
        for storage in self.configure['storage']:
            if storage['name'] == store_params['storage']:
                params = storage
                break
        return params

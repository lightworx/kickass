#!/usr/bin/env python
# coding=utf-8

from gflags import *
from BaseSpider import BaseSpider
from storage.mongodb import mongodb
from StoreBuilder import StoreBuilder
import subprocess, pymongo, yaml, time, redis
import re, md5, pycurl, StringIO, json


class url_collection(BaseSpider):

    def __init__(self,configure):
        self.configure = configure
        self.enable_break_process = FLAGS.enable_break_process
        self.cookie = FLAGS.cookie

    def get_collection(self,collection):
        print 'starting'
        for item in collection['collection']:
            start,end = item['range'].split('-')
            self.break_process = False
            for i in range(int(start),int(end)):
                url = item['url'].replace('{page}',str(i))
                self.parse_content(url,FLAGS.cookie,item['rules'])
                if self.break_process == True and self.enable_break_process == True:
                    break

    def parse_content(self,url,cookie,rules):
        print 'parse content'
        data_container = []
        try:
            html = self.get_content(url,cookie)
            html = html.replace("\n","")
            html = html.replace("\r","")
            if rules.has_key('method') and hasattr(url_collection,rules['method']): 
                data_container = getattr(self,rules['method'])(html)
            else: 
                attributes = re.findall(rules['rule'],html,re.M)
                for attribute in attributes:
                    dic = {}
                    for key, val in rules['attributes'].iteritems():
                        dic[key] = attribute[val]
                    data_container.append(dic)
            self.store_url(data_container)
        except Exception, e:
            pass

    def store_url(self,url):
        if isinstance(url,list):
            r = self.create_redis()
            self.insert_url(r,url)

    def insert_url(self,r,urls):
        self.break_process = True
        for url_item in urls:
            result = r.get(self.get_url_key(url_item['url'].encode('utf-8')))
            if result == None:
                self.break_process = False
                break

        if self.break_process == False:
            for url_item in urls:
                if url_item!=None:
                    url_item['crawl_time'] = time.time()
                    r.set(self.get_url_key(url_item['url'].encode('utf-8')),json.dumps(url_item))

    def create_redis(self,r=None):
        r = redis.Redis(connection_pool=POOL)
        return r

    # generate a url key for redis.
    def get_url_key(self,string):
        return self.configure['settings']['spider']+'_'+self.md5(string)

    def md5(self,string):
        return md5.new(string).hexdigest()

if __name__ == '__main__':

    DEFINE_string('configure','./rules/kickass.yaml','The spider configure.')
    DEFINE_string('base_url','http://kickass.to','The base URL.')
    DEFINE_string('cookie','','cookie')
    DEFINE_boolean('enable_break_process',False,'The option enable_break_process for switch the break_process.')
    DEFINE_list('store',['mysql','sqlite','mongodb','redis'],'The storage options.')
    
    try:
        sys.argv = FLAGS(sys.argv)
    except FlagsError,e:
        print '%s\nUsage:%s ARGS\n%s' % (e, sys.argv[0], FLAGS)
        sys.exit(1)

    configure = yaml.load(open(FLAGS.configure))
    storage_config = {}

    for storage in configure['storage']:
        if storage['name'] == 'redis':
            storage_config = storage
            break

    if configure['settings']['base_url']!=None:
        FLAGS.base_url = configure['settings']['base_url']
    if configure['settings']['cookie']!=None:
        FLAGS.cookie = configure['settings']['cookie']

    # creates an redis connection.
    POOL = redis.ConnectionPool(host=storage_config['host'],port=storage_config['port'],db=storage_config['db'])

    u = url_collection(configure)
    u.get_collection(configure)

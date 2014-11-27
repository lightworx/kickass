#!/usr/bin/env python
# coding=utf-8

from gflags import *
import sys
from BaseSpider import BaseSpider
from storage.mongodb import mongodb
from StoreBuilder import StoreBuilder
import subprocess, pymongo, yaml, time, redis, md5, pycurl, StringIO, json, re

class Spider(BaseSpider):
    def __init__(self,configure):
        self.configure = configure
        self.attributes = configure['attributes']
        self.cookie = FLAGS.cookie
        self.content_container = {}
        self.dbh = self.create_storage()
    
    def create_redis(self,r=None):
        return redis.Redis(connection_pool=POOL)

    def get_urls(self,base_url):
        url_container = []
        r = self.create_redis()
        for key in r.keys():
            item = r.get(key)
            try:
                item = json.loads(item.encode('utf-8').replace("'",'"'))
            except Exception, e:
                print item
            url_container.append(base_url+item['url'])
        return url_container

    def preprocess(self,html):
        return html.replace("\n","")

    def parse(self,base_url,storage):
        crawl_urls = self.get_urls(base_url) # Get the crawl urls from redis.
        content = ''
        # print crawl_urls
        for url in crawl_urls:
            try:
                content = self.preprocess(self.get_content(url,self.cookie))
                attributesContainer = self.parse_attributes(content)
                self.save_record(self.dbh,attributesContainer)
            except Exception as e:
                print("error")

    def match_all(self,rules,html):
        data_container = []
        attributes = re.findall(rules['rule'],html)
        for attribute in attributes:
             data_container.append(attribute[rules['position']-1])
        return data_container

    def position_content(self,html,position_range_rule,position=1):
        reContent = re.compile(position_range_rule)
        matched = reContent.search(html)
        if matched:
            return matched.group(position)

    def parse_attributes(self,content):
        attributesContainer = {}
        for attribute in self.attributes:
            # implementation starting position and ending position.
            if(attribute.has_key('content_range')==True and attribute.has_key('content_range_position')==True):
                content = self.position_content(attribute['content_range'],attribute['content_range_position'])

            if(attribute.has_key('multiple')==True and attribute['multiple']==True):
                matched = self.match_all(attribute,content)
            else:
                reContent = re.compile(attribute['rule'])
                matched = reContent.search(content)

            if matched:
                if attribute.has_key('multiple') and attribute['multiple'] == True:
                    attributesContainer[attribute['name']] = matched
                else:
                    attributesContainer[attribute['name']] = matched.group(attribute['position'])
        return attributesContainer

    def save_record(self,dbh,record):
        query = {"download_url":record['download_url']}
        record['rewrite_url'] = record['title'].lower().strip().replace(' ','-')
        dbh.data.update(query,record,upsert=True)
        # dbh.data.insert(record)

if __name__  == '__main__':
    DEFINE_string('configure','./rules/default.yaml','The spider configure.')
    DEFINE_string('cookie','','The spider cookie.')

    try:
        sys.argv = FLAGS(sys.argv)
    except FlagsError,e:
        print '%s\nUsage:%s ARGS\n%s' % (e, sys.argv[0], FLAGS)
        sys.exit(1)
    
    configure = yaml.load(open(FLAGS.configure))
    redis_config = {}
    mongo_config = {}

    for storage in configure['storage']:
        if storage['name'] == 'mongodb':
            mongo_config = storage
        if storage['name'] == 'redis':
            redis_config = storage

    POOL = redis.ConnectionPool(host=redis_config['host'],port=redis_config['port'],db=redis_config['db'])

    c = Spider(configure)
    c.parse(configure['settings']['base_url'],mongo_config)

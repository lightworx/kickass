#!/usr/bin/env python
# coding=utf-8

from pyquery import PyQuery as pq
from gflags import *
from BaseSpider import BaseSpider
import subprocess, pymongo, yaml
import time
from storage.mongodb import mongodb
from StoreBuilder import StoreBuilder

DEFINE_string('base_url','http://kickass.to','The base URL.')
DEFINE_string('configure','./rules/kickass.yaml','The spider configure.')
DEFINE_string('cookie','lang_detected=en; lang_code=en; captcha_hash=9410c0fbf30dc4963cb9451e2edab0b3; _spc=d17366a7-70ad-c92c-8d16-c76df2a35c5d; _ga=GA1.2.1569526442.1392654840; country_code=CN; state=1395237703988','The spider cookies.')
DEFINE_list('store',['mysql','sqlite','mongodb','redis'],'The storage options.')

class Spider(BaseSpider):
    def __init__(self):
        self.base_url = FLAGS.base_url
        self.cookie = FLAGS.cookie
        self.headers = []
        self.url_container = {}

    def run(self):
        self.get_rules()
        self.parse_rule()

    def get_rules(self):
        self.settings = yaml.load(open(FLAGS.configure))
        nodes = {}
        for node in self.settings['nodes']:
            nodes[node['name']] = node
        self.nodes = nodes
    
    def parse_rule(self):
        for node in self.nodes:
            configure = self.nodes[node]
            has_attach_item = False
            if 'attach_item' in configure:
                has_attach_item = True

            if 'start_url' in configure:
                start_url = configure['start_url']
                rule = configure['url_rule']
                self.parse_url(node,start_url,rule,has_attach_item)
        
        node_items = self.get_valid_time().keys() # Get the has valid_time nodes.
        self.get_uncrawl_urls(node_items)

    def parse_url(self,item_name,url,rule,has_attach_item=False,html_dom=None):
        url_container = []
        if(html_dom==None):
            html_dom = pq(self.get_content(url,self.cookie))
        doms = html_dom(rule)
            
        for dom in doms:
            url_container.extend([pq(dom).attr('href')])
        self.store_url(item_name,url_container)

        if has_attach_item==True and self.nodes[item_name].has_key('attach_item'):
            print "\n\n\n"
            attach_item_name = self.nodes[item_name]['attach_item']
            url_rule = self.nodes[attach_item_name]['url_rule']
            self.parse_url(attach_item_name,url,url_rule,False,html_dom)

    def get_uncrawl_records(self,nodes):
        store_builder = StoreBuilder(self.settings)
        dbh = store_builder.create_storage(self.settings['store_rules'],'homepage')
        records = dbh.urls.find(
            {"item":{"$in":nodes}},
            {"crawl_time":0}
        )
        print records.count()
        return records

    def get_uncrawl_urls(self,nodes):
        while True:
            records = self.get_uncrawl_records(nodes)
            for record in records:
                if self.nodes[record['item']].has_key('sub_item'):
                    item = self.nodes[record['item']]['sub_item']
                    url_rule = self.nodes[item]['url_rule']
                    self.parse_url(item,record['url'],url_rule)
            if records.count()==0:
                break

    def store_url(self,item_name,url):
        store_rule = self.nodes[item_name]['store_rule']
        store_builder = StoreBuilder(self.settings)
        store_builder.create_storage(self.settings['store_rules'],store_rule)
        store_builder.store_url(item_name,url)
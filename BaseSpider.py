#!/usr/bin/env python

from gflags import *
import subprocess, pymongo, yaml, time, pycurl, StringIO, gzip, cStringIO, chardet
from storage.mongodb import mongodb
import random

class BaseSpider(object):

    # Get all the nodes of contain has valid_time.
    def get_valid_time(self):
        valid_time_container = {}
        for node in self.nodes:
            if self.nodes[node].has_key('valid_time') and self.nodes[node]['valid_time']!='None':
                valid_time_container[node] = self.nodes[node]
        return valid_time_container

    def get_content(self,url,cookie=[]):
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL,url)
        curl.setopt(pycurl.HTTPHEADER, self.header_builder())
        curl.setopt(pycurl.COOKIE, cookie)
        b = StringIO.StringIO()
        curl.setopt(pycurl.WRITEFUNCTION, b.write)
        curl.setopt(pycurl.FOLLOWLOCATION, 1)
        curl.setopt(pycurl.MAXREDIRS, 5)
        curl.setopt(pycurl.SSL_VERIFYPEER, False)
        curl.setopt(pycurl.SSL_VERIFYHOST, False)
        # set the encoding option enable, the value to gzip,like this
        # curl.setopt(pycurl.CURLOPT_ENCODING, 'gzip')
        # http://www.nowamagic.net/librarys/veda/detail/1770
        curl.perform()
        curl.close()
        html = b.getvalue()
        if html[:6] == '\x1f\x8b\x08\x00\x00\x00':
           html = gzip.GzipFile(fileobj = cStringIO.StringIO(html)).read()
        html = self.convert_coding(html)
        return html

    def convert_coding(self,html):
        file_info = chardet.detect(html)
        unicode_str = html.decode(file_info['encoding'])
        html = unicode_str.encode('utf-8')
        return html

    def header_builder(self):
        userAgents = [
            'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36',
            'user-agent: Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0)'
        ]
        userAgentItem = random.randint(0,1)
        headers = ['Pragma: no-cache',
        'Accept-Encoding: gzip,deflate,sdch',
        'Accept-Language: en-US,en;q=0.8',
        userAgents[userAgentItem],
        # 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36',
        'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Connection: keep-alive',
        'Cache-Control: no-cache']
        headers.extend(['Cookie: '+self.cookie])
        return headers

    def create_storage(self):
        for storage in self.configure['storage']:
            if storage['driver']=='mongodb':
                break
        
        mongo = mongodb(self.configure)
        dbh = mongo.connect(storage)
        return dbh
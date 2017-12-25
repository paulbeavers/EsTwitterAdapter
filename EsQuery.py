#!/usr/bin/python

import time
import sys
import tweepy
import json
import pycurl
import re
import logging
import logging.handlers
from StringIO import StringIO

#----------------------------------------------------
# Global Configuration Variables
#----------------------------------------------------

headers = ['Expect:', 'Content-Type: application/json']

buffer = StringIO()
c = pycurl.Curl()

url = 'http://localhost:9200/twitter/tweet/_search?pretty'

newQuery = {  "from" : 0, "size" : 10000,
              "query":
              { 
                  "match":
                  {  
                      "tweetText": "apple" 
                  } 
              }
           } 

c.setopt(pycurl.HTTPHEADER,headers )
c.setopt(pycurl.URL, url)
data = json.dumps(newQuery)
c.setopt(pycurl.POSTFIELDS,data)
c.setopt(c.WRITEDATA, buffer)

try:
   c.perform()
   http_code = c.getinfo(pycurl.HTTP_CODE)
except Exception, e:
   self.mlog.warning(e)
   c.close()

body = json.loads(buffer.getvalue())

print body

for doc in body['hits']['hits']:
   print "-----------------------------------------" 
   print doc['_source']['tweetText']





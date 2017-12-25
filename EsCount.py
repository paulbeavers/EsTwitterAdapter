#!/usr/bin/python

import json
import pycurl
from StringIO import StringIO

headers = ['Expect:', 'Content-Type: application/json']

buffer = StringIO()
c = pycurl.Curl()

url = 'http://localhost:9200/twitter/tweet/_count'

c.setopt(pycurl.HTTPHEADER,headers )
c.setopt(pycurl.URL, url)
c.setopt(c.WRITEDATA, buffer)

try:
   c.perform()
   http_code = c.getinfo(pycurl.HTTP_CODE)
except Exception, e:
   print e
   c.close()

body = json.loads(buffer.getvalue())
print body['count']


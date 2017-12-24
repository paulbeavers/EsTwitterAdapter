#!/usr/bin/python

import time
import sys
import tweepy
import json
import pycurl
from multiprocessing import Pool
from threading import Thread
from Queue import Queue
import threading
import re
import logging
import logging.handlers
from StringIO import StringIO

#----------------------------------------------------
# Global Configuration Variables
#----------------------------------------------------
filterString = "apple,BMC"
LOG_FILENAME = "/home/pbeavers/EsTwitterAdapter/EsTwitterAdapter.log"
consumer_key = "xPvkJIWwnsNPvC4jshG94aOkt"
consumer_secret = "UgsCptyim8DCRE9a8zjyXI1wnhWPfDCkJMZnlscddOiSVTjFxM"
access_token_key = "160202734-YXkLuLlq9B1qXsulB59RLKAUvfBzU4TQ37WtRO9j"
access_token_secret = "NTAAVxQ0GhVTiF0y0keLb9LNPDbfGkDFmBbHO1F49EFYm"

#---------------------------------------------------
# Thread class for processing
#---------------------------------------------------
class Worker(Thread):
        """Thread executing tasks from a given tasks queue"""
        def __init__(self, tasks):
            Thread.__init__(self)
            self.tasks = tasks
            self.daemon = True
            self.start()

        def run(self):
            while True:
                func, args, kargs = self.tasks.get()
                try:
                    func(*args, **kargs)
                except Exception, e:
                    print e
                finally:
                    self.tasks.task_done()

class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads): Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()


#---------------------------------------------------
# Listener for tweepy stream
#---------------------------------------------------
class CustomStreamListener(tweepy.StreamListener):
    
    continueThread = 1
    tweetCounter = 0

    t = 0

    #--------------------------------------------------
    # Raise event function to post events to Pulse
    #--------------------------------------------------
    def raiseEvent(self, tweetText, userName, uniqueId):

        headers = ['Expect:', 'Content-Type: application/json']
        url =  "https://api.truesight.bmc.com/v1/events"

        newEvent = {
                "uniqueID": uniqueId,
                "tweetText": tweetText,
                "tweetUser": userName
                }

        buffer = StringIO()
        c = pycurl.Curl()

        strID = str(uniqueId)
        url = 'http://localhost:9200/twitter/tweet/' + strID
        headers = ['Expect:', 'Content-Type: application/json']

        c.setopt(pycurl.HTTPHEADER,headers )
        c.setopt(pycurl.URL, url)
        data = json.dumps(newEvent)
        c.setopt(pycurl.POSTFIELDS,data)
        c.setopt(c.WRITEDATA, buffer)


        try:
           c.perform()
           http_code = c.getinfo(pycurl.HTTP_CODE)
           self.mlog.debug("status code: %s" % http_code)
        except Exception, e:
           self.mlog.warning(e)
        c.close()

        body = buffer.getvalue()

    #---------------------------------------------------
    # Call back for RaiseEvent
    #---------------------------------------------------

    def __init__(self):

        self.pool = ThreadPool(20)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.mlog = logging.getLogger('MyLogger')
        self.mlog.setLevel(logging.DEBUG)
        self.handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=100000000, backupCount=5)
        self.handler.setFormatter(formatter)
        self.mlog.addHandler(self.handler)
        self.mlog.debug("__init__() for CustomStreamListener.")

	self.mlog.debug("Hello world")
        self.seed_uid = int(time.time())

    #--------------------------------------------------------------------------
    # Our main processing object is a sublass of Tweepy's stream listener
    # we do not have a need for the on_status method so it is commented out
    #--------------------------------------------------------------------------

    def on_status(self, status):
        self.mlog.debug("Received on_status callback")

    #--------------------------------------------------------------------------
    # Our main processing object is a sublass of Tweepy's stream listener
    # The on_data method is invokded when a tweet satisfying the given filter
    # is received.
    #--------------------------------------------------------------------------
    def on_data(self, data):
        self.mlog.debug("Received on_data callback")
        tweet = json.loads(data)
        if tweet.has_key('user'):
             user = tweet['user']['name']
             text = tweet['text']
             decoded_user = user.encode('utf-8')
             decoded_string = text.encode('utf-8')
             decode_string = decoded_string.decode('string_escape')
             decode_user = decoded_user.decode('string_escape')

             self.tweetCounter = self.tweetCounter + 1
             self.seed_uid = self.seed_uid + 1
             self.pool.add_task(self.raiseEvent,decoded_string,decoded_user, self.seed_uid)

    def on_error(self, status_code):
        self.mlog.warning("Received on_error call back")
        self.mlog.warning("on_error() encountered error with status code: " + str(status_code))
        return True # Don't kill the stream

    def on_timeout(self):
        self.mlog.warning("Receidved on_timeout callback")
        self.mlog.warning("on_timeout() timeout triggered.  Not killing stream.")
        return True # Don't kill the stream

    def __del__(self):
        self.continueThread = 0
        time.sleep(4)
        self.mlog.info("killing thread")
        self.pool.wait_completion()


#------------------------------------------------------------------------
# Main
#-----------------------------------------------------------------------

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token_key, access_token_secret)
sapi = tweepy.streaming.Stream(auth, CustomStreamListener())

filterArray = filterString.split(",")

sapi.filter(track=filterArray, languages=["en"])



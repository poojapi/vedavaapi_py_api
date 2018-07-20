from config import *
import random
import sys,os
from mydb import *
from pprint import pprint
from resources.collections import *

class SubantaRsrc(CollectionRsrc):
    def __init__(self):
        self.cname = 'subantas'
        self.key = ['word']
        self.schema = {
            'encoding' : '',
            'word': '',
            'type': '',
            'subtype': '',
            'linga': '',
            'meaning': '',
            'context': '',
            'subcontext': '',
            'audio_url': '',
            'image_url': '',
            'forms' : ''
        }
        CollectionRsrc.__init__(self, samvit().db()[self.cname])

class TinantaRsrc(CollectionRsrc):
    def __init__(self):
        self.cname = 'tinantas'
        self.key = ['word']
        self.schema = {
            'encoding' : '',
            'word': '',
            'type': '',
            'subtype': '',
            'padi': '',
            'meaning': '',
            'context': '',
            'subcontext': '',
            'audio_url': '',
            'image_url': '',
            'forms' : ''
        }
        CollectionRsrc.__init__(self, samvit().db()[self.cname])

class TemplatesRsrc(CollectionRsrc):
    def __init__(self):
        self.cname = 'phrase_templates'
        self.key = ['name']
        self.schema = {
            'encoding' : '',
            'template_name': '',
            'samvit_levelid' : '',
            'parms': [],
            'vaakya' : '',
            'components': []
        }
        CollectionRsrc.__init__(self, samvit().db()[self.cname])

class WordClustersRsrc(CollectionRsrc):
    def __init__(self):
        self.cname = 'word_clusters'
        #self.key = ['name']
        self.schema = {
            'template_name': '',
            'encoding':'',
            'samvit_levelid' : '',
            'word1': '',
            'word2': '',
            'word3': '',
            'word4': '' 
        }
        CollectionRsrc.__init__(self, samvit().db()[self.cname])

class ExerciseRsrc(CollectionRsrc):
    def __init__(self):
        self.cname = 'word_clusters'
        #self.key = ['name']
        self.schema = {
            'exercise_template_id': '',
            'encoding':'',
            'samvit_levelid' : '',
            'parms': '',
            'c1': '',
            'c2': '',
            'c3': '',
            'c4': '',
            'c5': '',
            'c6': '',
        }
        CollectionRsrc.__init__(self, samvit().db()[self.cname])

class _Samvit:
    def __init__(self, reset=False):
        self._db = MYMongoDB(serverconfig()['samvit_db'])
        if reset:
            self.db().reset()
        self.collections = ['subantas', 'tinantas', 'phrase_templates',
            'phrase_words', 'exercise_templates']

        for cname in self.collections:
            if cname not in self.db():
                self._load(cname)

    def _load(self, cname):
        csvfile = cmdpath(cname + ".csv")
        if os.path.isfile(csvfile):
            print "Loading {} bank from {}".format(cname, csvfile)
            collection = self.db()[cname]
            collection.fromCSV(csvfile)
        else:
            print "Skipped missing {} bank in {}".format(cname, csvfile)
            

    def db(self):
        return self._db

_samvit = None
def samvit(reset=False):
    global _samvit
    if not _samvit:
        _samvit = _Samvit(reset)
    return _samvit

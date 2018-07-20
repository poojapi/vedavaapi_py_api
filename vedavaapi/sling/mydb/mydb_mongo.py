from pymongo import MongoClient
from pymongo.database import Database
import sys
from .mydb import *

from operator import itemgetter, attrgetter, methodcaller

class MYMongoDBCollection(MYDBTable):
    def __init__(self, name, mydb):
        self.mongo_collection = mydb[name]
        
    def all(self):
        return self.mongo_collection.find()
        
    def count(self):
        return self.mongo_collection.count()
        
    def reset(self):
        return self.mongo_collection.drop()
        
    def find_one(self, query):
        return self.mongo_collection.find_one(query)
        
    def insert_one(self, item):
        return self.mongo_collection.insert_one(item)
        
    def update(self, query, mod_spec):
        return self.mongo_collection.update(item)

class MYMongoDB(MYDB):
    def initialize(self):
        try:
            self.client = MongoClient()
            self.db = self.client[self.dbname]
        except Exception as e:
            print("Error initializing MongoDB database; aborting.", e)
            raise e

        if not isinstance(self.db, Database):
            raise TypeError("database must be an instance of 'Database'")

    def reset(self):
        print "Clearing database", self.dbname
        self.client.drop_database(self.dbname)
        self.initialize()

    # Find or create given collection within a MongoDB database
    def get_collection(self, collection_name):
        return MYMongoDBCollection(collection_name, self.db)

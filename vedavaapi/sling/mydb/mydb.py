import re
import sys
import csv

from bson.objectid import ObjectId
import json
from operator import itemgetter, attrgetter, methodcaller
            
def table2json(t):
    return [dict(zip(t['fields'], valrow)) for valrow in t['values']]

# Base class to encapsulate a MYDB Table
class MYDBTable:
    def __init__(self, name, mydb):
        self.mydb = mydb
        self.dbtable = None
        
    def all(self):
        raise TypeError("No method definition available: MYDBTable.all.")
        
    def count(self):
        raise TypeError("No method definition available: MYDBTable.count.")
        
    def reset(self):
        raise TypeError("No method definition available: MYDBTable.reset.")
        
    def find_one(self, query):
        raise TypeError("No method definition available: MYDBTable.find_one.")
        
    def insert_one(self, item):
        raise TypeError("No method definition available: MYDBTable.insert_one.")
        
    def update(self, query, mod_spec):
        raise TypeError("No method definition available: MYDBTable.update.")
        
# MYDB collection with import/export functionality
class MYDBCollection:
    def __init__(self, name, dbtable, cache=False):
        self.name = name
        self.dbtable = dbtable
        self.cache = cache
        self.local = None
        self.schema = None
        if cache:
            self.slurp()

    def slurp(self):
        self.local = {}
        for o in self.dbtable.find():
            o['_id'] = str(o['_id'])
            self.local[o['_id']] = o

        return self.local

    def all(self):
        if not self.local:
            self.slurp()
        return self.local

    def count(self):
        return self.dbtable.count()

    def toJSON(self):
        return { self.name : self.slurp() }

    def fromJSON(self, data):
        self.dbtable.drop()
        if data:
            # Save the first row contents as schema table 
            # after emptying its values.
            self.schema = data[0]
            for k in self.schema.keys():
                self.schema[k] = ''
        try:
            for d in data:
                self.insert(d)
        except Exception as e:
            print "Error inserting into " + self.name + ": ", e
        if self.cache:
            self.slurp()

    def fromCSV(self, fname, primarykey = None):
        table = {'name' : self.name}
        with open(fname) as f:
            gothdr = False
            idx = {}
            primaryidx = None
            for row in csv.reader(f):
                if not gothdr:
                    gothdr = True
                    row[0] = row[0].lstrip('#')
                    idx = dict(zip(row, range(len(row))))
                    table['fields'] = []
                    table['fields'].extend(row)
                    if primarykey:
                        table['fields'].append('_id')
                        primaryidx = idx[primarykey]

                    table['values'] = []
                    continue
                if row[0].startswith('#'):
                    continue
                #print [re.split(r'\s*,\s*', r) for r in row if ',' in r]
                row = map(lambda x: re.split(r',\s*', x) if ',' in x else x, row)
                values = row
                #print row
                if primarykey:
                    values.append(values[primaryidx])
                table['values'].append(values)
            self.fromJSON(table2json(table))

    def __repr__(self):
        return json.dumps(self.toJSON())

    def oid(self, item_id):
        try:
            return {'_id' : ObjectId(item_id)}
        except Exception as e:
            print "Error: invalid object id ", e
            return None

    def get(self, item_id):
        res = self.local[item_id] if self.cache else None
        if not res:
            query = self.oid(item_id)
            if not query:
                return None
            res = self.dbtable.find_one(query)
            if res:
                res['_id'] = str(res['_id'])
        return res

    def find_one(self, query):
        res = self.dbtable.find_one(query)
        if res:
            res['_id'] = str(res['_id'])
        return res

    def insert(self, item):
        #print "Inserting",item
        try:
            result = self.dbtable.insert_one(item)
        except Exception as e:
            print "Error inserting into " + self.name + ": ", e
            return None
        return str(result.inserted_id)

    def update(self, item_id, fields):
        query = self.oid(item_id)
        if not query:
            return False
        result = self.dbtable.update(query, {"$set" : fields})
        isSuccess = (result['n'] > 0)
        return isSuccess

    def delete(self, item_id):
        query = self.oid(item_id)
        if not query:
            return False
        res = self.dbtable.delete_one(query)
        if res:
            return res.deleted_count > 0
        else:
            return False

    def reset(self):
        return self.dbtable.drop()

    def find(self, query = {}, fields = []):
        if len(fields) > 0:
            f = dict((k, 1) for k in fields)
            return self.dbtable.find(query, f)
        else:
            return self.dbtable.find(query)

    def __exit__(self, type, value, traceback):
        return True

# Wrapper class for a persistent database
class MYDB:
    def __init__(self, dbname):
        self.dbname = dbname
        self.db = None
        self.c = {}
        self.initialize()
#        if not database.write_concern.acknowledged:
#            raise ConfigurationError('database must use '
#                                     'acknowledged write_concern')

    def __getattr__(self, name):
        if name not in self.c:
            self.add_collection(name)
        return self.c[name]

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __contains__(self, name):
        return name in self.c

    def add_collection(self, cname, cache=False):
        collection = MYDBCollection(cname, self.db[cname], cache)
        self.c[collection.name] = collection

    # List all the collections / tables in the database
    def list(self):
        return self.c.keys()

    def initialize(self):
        raise TypeError("No method definition available: MyDB.initialize.")

    def reset(self):
        raise TypeError("No method definition available: MyDB.reset.")

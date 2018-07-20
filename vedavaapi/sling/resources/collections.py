from flask import request
from flask_restplus import fields, abort, marshal, Resource
import pymongo
#from ..db import *
import re
from pprint import pprint

class _Rsrc_url(fields.Raw):
    cname = None
    def format(self, id):
        return '/{}/{}'.format(self.cname, id) if id else ''
    def id(self, url):
        match = re.search('/([^/]*)$'.format(self.cname), url)
        return match.group(1) if match else None

attr2external = {
}

class CollectionRsrc(Resource):
    schema = {}
    cname = None
    key = None
    mycollection = None

    def __init__(self, collection):
        self.mycollection = collection
        for u in self.mycollection.find():
            if not self.schema:
                self.schema = u
                #self.attrs.pop('_id')
            break
        self.schema_ext = {}

        self.exported_fields = {}

        # Externalize the schema field names
        for a in self.schema.keys():
            m = re.search('^(.*?)_id$', a)
            if m:
                repl_a = m.group(1) + '_url'
                v = self.schema[a]
                self.schema_ext[repl_a] = v
            else:
                self.schema_ext[a] = self.schema[a]

        for a in self.schema.keys():
            if a in attr2external:
                for k, v in attr2external[a].items():
                    self.exported_fields[k] = v 
            else:
                self.exported_fields[a] = fields.String
        self.exported_fields['_url'] = \
            fields.FormattedString('/' + self.cname + '/{_id}')

    def put(self, _id):
        print "Updating {} by {} ".format(self.cname,  _id)
        args = request.json
        for k, v in args.items():
            if (k == '_id') or not v:
                args.pop(k)

        print "Update args ..."
        pprint(args)
        self.sanitize(args)
        print "Sanitized args ..."
        pprint(args)

        self.set_defaults(args)
        if self.mycollection.update(_id, args):
            entry = self.mycollection.get(_id)
            return marshal(entry, self.exported_fields)
        else:
            abort(404)
    
    def delete(self, _id):
        if self.mycollection.delete(_id):
            return {}
        else:
            abort(404)

    def sanitize(self, entry):
        for k in entry:
            if entry[k] in ['null', 'undefined']:
                entry[k] = ''

    def post(self):
        print "Inserting into {} ".format(self.cname)

        args = request.json
        print "Post args ..."
        pprint(args)
        self.sanitize(args)

        print "Sanitized args ..."
        pprint(args)

        for k, v in args.items():
            if (k == '_id') or not v:
                args.pop(k)
        self.set_defaults(args)

        _id = None
        if self.key:
            q = dict((k, args[k]) for k in self.key if k in args)
            e = self.mycollection.find_one(q)
            if e:
                _id = e['_id']
                self.mycollection.update(_id, args)
        if not _id:
            _id = self.mycollection.insert(args)

        entry = self.mycollection.get(_id)
        return marshal(entry, self.exported_fields), 201

    def default(self, k):
        if k not in self.schema:
            return None
        val = self.schema[k]['default'] if isinstance(self.schema[k], dict) \
                else self.schema[k]

    def set_defaults(self, entry):
        missing_keys = []
        for k, v in self.schema.items():
            if k not in entry:
                missing_keys.append(k)
                entry[k] = self.default(k)

    def mymarshal(self, output, fields = None):
        # Remove fields not present in out_entry
        #pprint(output)

        inlist = output if isinstance(output, list) else [output]

        for e in inlist:
            self.set_defaults(e)

        try:
            r = marshal(output, self.exported_fields)
            if isinstance(r, list):
                for row in r:
                    for k, v in row.items():
                        if fields and (k not in fields or not v):
                            row.pop(k)
            else:
                    for k, v in r.items():
                        if fields and (k not in fields or not v):
                            r.pop(k)
            return r
        except Exception as e:
            print "Error in mymarshal: ", e
            return {}

    def get(self, _id=None):
        if 'schema' in request.url_rule.rule:
            print "Schema returned", self.schema_ext
            return self.schema_ext

        if _id:
            print "Retrieving {} by {} ".format(self.cname,  _id)
            entry = self.mycollection.get(_id)
            if entry:
                return self.mymarshal(entry)
            else:
                abort(404)
        else:
            print "Listing " + self.cname
            args = request.args.copy()
            self.sanitize(args)
            exact = False
            distinct = None
            if 'distinct' in args:
                distinct = args['distinct']
                args.pop('distinct')
            if 'exact' in args:
                exact = True if int(args['exact']) > 0 else False
                args.pop('exact')
            offset = args['offset'] if 'offset' in args else 0
            offset = args['offset'] if 'offset' in args else 0
            if 'offset' in args:
                args.pop('offset')
            limit = args['limit'] if 'limit' in args else 0
            if 'limit' in args:
                args.pop('limit')
            fields = None
            if 'fields' in args and args['fields'] != '':
                fields = args['fields'].split(',')
                pprint(fields)
                args.pop('fields')

            query = {}
            for k, v in args.items():
                if k == 'Region_id' or not v:
                    args.pop(k)
                    continue
                if exact:
                    query[k] = { '$regex' : '^{}$'.format(v), '$options' : 'i' }
                else:
                    query[k] = { '$regex' : v, '$options' : 'i' }
            pprint(query)
            if distinct:
                elist = [e for e in self.mycollection.collection.distinct(distinct, query)]
                return {distinct : elist}
            else:
                elist = [e for e in self.mycollection.find(query) \
                    .sort('_id', pymongo.ASCENDING).skip(offset).limit(limit)]
            return self.mymarshal(elist, fields)

from flask_restplus import Resource
from pprint import pprint

class _Types(Resource):
    cname = None

    def get(self):
        if not self.cname:
            abort(404)
        coll = dbget()[self.cname]
        return sorted(coll.all().keys())

class Presets(Resource):
    _presets = {}
    _indices = {}
    _keys = {}

    def idx(self, a, v):
        if a not in self._indices:
            vals = self._presets[a]
            self._indices[a] = dict(zip(vals, range(len(vals))))
            #pprint(self._indices[a])
        return self._indices[a][v]
        
    def get(self, field=None):
        if field:
            if field in self._presets:
                return self._presets[field]
            else:
                return []
        else:
            #print self._presets.keys()
            if not self._keys:
                self._keys = sorted(self._presets.keys())
            return self._keys

if __name__ == "__main__":
    p = Presets()

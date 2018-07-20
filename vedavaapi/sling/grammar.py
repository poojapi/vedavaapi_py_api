from config import *
import requests
from mydb import *
from resources.types import *
from resources.collections import *
import json
from pprint import pprint
import sys, locale, os
import re

def _missing_args(reqd, args):
    x = filter(lambda a: a not in args, reqd)
    #print x
    if x:
        print 'input args = ', args
        print 'reqd = ', reqd
        print 'missing = ', x
    return x

def purusha(subanta, encoding):
    return grammar().purusha(subanta, encoding)

class SktPresets(Presets):
    _presets = {
        'prayoga' :
            ['kartari', 'karmaNi'],
        'linga' :
            ['puM', 'strI', 'napuM'],
        'vachana' :
            ['eka', 'dvi', 'bahu'],
        'lakara' :
            ['laT', 'liT', 'luT', 'lR^iT', 'loT', 'la~N', 'vidhili~N', 'AshIrli~N', 'lu~N', 'lR^i~N'],
        'purusha' :
            ['prathama', 'madhyama', 'uttama'],
        'padi' :
            ['Atmane', 'parasmai', 'ubhaya'],
        'type' :
            ['subanta', 'ti~Nanta'],
        'subtype' :
            ['kR^idanta', 'taddhita'],
        'vibhakti' :
            [1, 2, 3, 4, 5, 6, 7, 8],
#            ['prathamA', 'dvitIyA', 'tR^itIyA', 'chaturthI', 'pa~nchamI',
#            'ShaShThI', 'saptamI', 'saM prathamA'],
        'encoding' :
            ['WX', 'Itrans', 'Unicode', 'VH', 'SLP', 'KH', 'Roman'],
        'script' :
            ['Devanagari', 'Telugu', 'Kannada', 'Tamil', 'Malayalam'],
    }

_grammar = None
def grammar(reset=False):
    global _grammar
    if not _grammar:
        _grammar = Grammar(reset)
    return _grammar

class Dhaatus(CollectionRsrc):
    def __init__(self):
        self.cname = 'dhaatus'
        self.key = ['root']
        self.schema = {
            'root': '',
            'dhatu': '',
            'gana': '',
            'meanings': '' }
        CollectionRsrc.__init__(self, grammar().db()[self.cname])

class Cache_nounforms(CollectionRsrc):
    def __init__(self):
        self.cname = 'cache_nounforms'
        self.key = ['root']
        self.schema = {
            'root': '',
            'linga': '',
            'forms': '' }
        CollectionRsrc.__init__(self, grammar().db()[self.cname])

class Grammar:
    code2wx = {
        'VH' : ["converters/velthuis-wx.out"],
        'KH' : ["converters/kyoto_ra.out"],
        'SLP' : ["converters/slp2wx.out"],
        'Itrans' : ["converters/itrans_ra.out"],
        'Unicode' : ["converters/utf82iscii.pl", "converters/ir_skt"],
        'Roman' : ["converters/utf8roman2wx.out"],
    }

    wx2code = {
        'VH' : ["converters/wx-velthuis.out"],
        'KH' : ["converters/ra_kyoto.out"],
        'SLP' : ["converters/wx2slp.out"],
        'Itrans' : ["converters/ra_itrans.out"],
        'Unicode' : ["converters/ri_skt", "converters/iscii2utf8.py 1"],
        'Roman' : ["converters/wx2utf8roman.out"],
    }

    presets = SktPresets()
    word_attrs = None
    _db = None

    def __init__(self, reset=False):
        self._db = MYMongoDB(serverconfig()['grammar_db'])
        if reset:
            self.db().reset()
        if 'dhaatus' not in self.db().c:
            self.db().dhaatus.fromCSV(cmdpath("dhaatu_list.csv"), "root")
        self.word_attrs = [p for p in self.presets.get() if p not in ['encoding', 'script']]

    def db(self):
        return self._db

    def purusha(self, subanta, encoding):
        subanta_itx = self.xcode(subanta, encoding, 'Itrans')
        if subanta_itx in ['aham', 'AvAm', 'vayam']:
            return self.xcode('uttama', 'Itrans', encoding)
        elif subanta_itx in ['tvam', 'yuvAm', 'yUyam']:
            return self.xcode('madhyama', 'Itrans', encoding)
        else:
            return self.xcode('prathama', 'Itrans', encoding)

    def _xcode_cmd(self, in_encoding, out_encoding = 'Unicode'):
        if in_encoding == out_encoding:
            return None

        conv_seq = []
        if in_encoding != 'WX' and in_encoding in self.code2wx:
            conv_seq.extend(self.code2wx[in_encoding])
        if out_encoding != 'WX' and out_encoding in self.wx2code: 
            conv_seq.extend(self.wx2code[out_encoding])
        cmd = "| ".join(map(lambda c: self.cpath(c), conv_seq))
        return cmd

    def xcode_str(self, text, in_encoding, out_encoding = 'Unicode'):
        if in_encoding == out_encoding:
            return text

        xcode_cmd = self._xcode_cmd(in_encoding, out_encoding)
        cmd = "echo \"{}\" | {}".format(text, xcode_cmd)
        out = self.do_local(cmd)
        out = re.sub('##','', out)
        return out.rstrip().decode('utf-8')

    def xcode(self, text, in_encoding, out_encoding = 'Unicode'):
        #print "in_encoding {}, out_encoding {}, text {}".format(in_encoding, out_encoding, text)
        if in_encoding == out_encoding:
            return text

        if isinstance(text, list):
            return [self.xcode(e, in_encoding, out_encoding) for e in text]
        elif isinstance(text, dict):
            mydict = {}
            for p in text.keys():
                mydict[p] = self.xcode(text[p], in_encoding, out_encoding)
            return mydict
        else:
            return self.xcode_str(text, in_encoding, out_encoding)

    def xcode_api(self, args):
        m = _missing_args(['text', 'encoding', 'out_encoding'], args)
        if m:
            return {'status' : 'Missing arguments: ' + ", ".join(m)}

        out_encoding = args['out_encoding']

        res = self.xcode(args['text'], args['encoding'], out_encoding)
        return { 'status' : 'ok', 'result' : res }
    
    def cpath(self, cmd):
        return join(serverconfig()['scl_path'], cmd)

    def do_remote(self, url):
        response = requests.get(url)

    def do_local(self, cmd, encoding_in = 'Unicode', out_encoding = None):
        if not out_encoding:
            out_encoding = encoding_in
        xcode_cmd = self._xcode_cmd('Unicode', out_encoding)
        if xcode_cmd:
            cmd += "|" + xcode_cmd
        #print cmd
        try:
            output = mycheck_output(cmd)
            #print output
            if output:
                output = re.sub('##', '', output)
                output = re.sub('@', '', output)
                pass
        except Exception as e:
            print "Error executing command:", e
            return None
        return output

    def analyze_api(self, parms):
        outstr = self.do_local("{} {} {} LOCAL json".format( \
            self.cpath("SHMT/prog/morph/callmorph.pl"), parms['word'], \
                'WX'), out_encoding = 'WX')
        o = json.loads(outstr)
        return o

    def analyze(self, args, out_encoding = None):
        m = _missing_args(['word', 'encoding'], args)
        if m:
            return {'status' : 'Missing arguments: ' + ", ".join(m)}
        if not out_encoding:
            out_encoding = args['out_encoding'] if 'out_encoding' in args else args['encoding']
        word_wx = self.xcode(args['word'], args['encoding'], 'WX')
        o = self.cached_api({'api' : 'analyze_api', 'word' : word_wx}, 
                out_encoding)
        if 'result' not in o:
            return {'status' : 'Error: could not analyze word {}'.format(args['word'])}
        #print "self.analyze args = ", args
        filters = dict((k, self.xcode(v, args['encoding'], out_encoding)) \
                        for k,v in args.items() \
                            if k in self.word_attrs)
        #print "self.analyze filter = ", filters
        if any(filters):
            matches = []
            #print "analyze: ",filters
            for a in o['result']:
                #print 'result = ',a
                found = True
                for k,v in filters.items():
                    if k in a and a[k] != v:
                        #print "Missing attr = ",k
                        found = False
                        break
                if found:
                    matches.append(a)
            o['result'] = matches
            for k,v in filters.items():
                o[k] = v
        o['out_encoding'] = out_encoding
        o['status'] = 'ok'
        if '_output' in o:
            del o['_output'] 
        return o

    def noun_forms_api(self, parms):
        cmd = "{} {} {} {} {} {} LOCAL json".format( \
            self.cpath("skt_gen/noun/gen_noun.pl"), parms['root'],
            parms['linga'], 'WX', 'WX', parms['level'])
        outstr = self.do_local(cmd, out_encoding='WX')

        o = json.loads(outstr)
        #pprint(o)
        if 'result' in o:
            return o
        else:
            return {'status' : 'Error: could not generate noun forms of root {}'.format(parms['root'])}

    def noun_forms(self, args, out_encoding=None, level=1):
        m = _missing_args(['root', 'encoding', 'linga'], args)
        if m:
            return {'status' : 'Missing arguments: ' + ", ".join(m)}
        encoding_in = args['encoding']
        if not out_encoding:
            out_encoding = args['out_encoding'] if 'out_encoding' in args else encoding_in
        root_wx = self.xcode(args['root'], encoding_in, 'WX')
        linga_wx = self.xcode(args['linga'], encoding_in, 'WX')
        o = self.cached_api({'api' : 'noun_forms_api', 
            'root' : root_wx, 'linga' : linga_wx, 'level' : 1}, out_encoding)
        if 'result' not in o:
            return {'status' : 'Error: could not generate verb forms of root {}'.format(args['root'])}

        res = o['result']
        for parm in ['vibhakti', 'vachana']:
            if parm in args and args[parm] != '':
                v = self.xcode(args[parm], encoding_in, 'Itrans')
                v = self.presets.idx(parm, v)
                res = res[v]
                o[parm] = self.xcode(args[parm], encoding_in, out_encoding)
            else:
                o[parm] = [self.xcode(v, encoding_in, out_encoding) \
                    for v in self.presets.get(parm)]
                break
        o['out_encoding'] = out_encoding
        o['result'] = res
        o['status'] = 'ok'
        if '_output' in res:
            del res['_output'] 
        return o

    def verb_forms_api(self, parms):
        entry = self.db().dhaatus.find({'_id' : parms['root']})
        for e in entry:
            #pprint(e)
            words = " ".join([e['root'], e['dhatu'], e['gana'], e['meanings']])
            rt_spec = words.replace(' ', '_')
            outstr = self.do_local("{} {} {} {} LOCAL json".format(self.cpath("skt_gen/verb/gen_verb.pl"), "WX", parms['prayoga'], rt_spec), out_encoding='WX')
            o = json.loads(outstr)
            #pprint(o)
            if 'result' in o:
                return o
            else:
                return {'status' : 'Error: could not generate verb forms of root {}'.format(args['root'])}
            break
        return {'status' : 'Error: root {} not found'.format(parms['root'])}

    # Invoke an API with given parms supplied; Assume 'WX' notation
    def cached_api(self, parms, out_encoding='WX'):
        o =  self.db().api_cache.find_one(parms)
        if o:
            #print "API Cache Hit: ", parms['api']
            pass
        else:
            #print "API Cache Miss: ", parms['api']
            api_func = getattr(self, parms['api'])
            o = api_func(parms)
            if 'result' in o:
                #print "Caching forms_wx: ", o['result']
                entry = parms.copy()
                entry['result'] = o['result']
                self.db().api_cache.insert(entry)
                o =  self.db().api_cache.find_one(parms)
                del o['_id']
                o['in_encoding'] = 'WX'
                o['out_encoding'] = 'WX'
            else:
                return o

        for p in o.keys():
            if p not in ['in_encoding', 'out_encoding', 'api']:
                #print p, o[p]
                o[p] = self.xcode(o[p], 'WX', out_encoding)
        #pprint (o['result'])
        return o


    def verb_forms(self, args, out_encoding = None):
        m = _missing_args(['root', 'encoding', 'prayoga'], args)
        if m:
            return {'status' : 'Error: Missing arguments: ' + ", ".join(m)}

        encoding_in = args['encoding']
        if not out_encoding:
            out_encoding = args['out_encoding'] if 'out_encoding' in args else encoding_in

        root_wx = self.xcode(args['root'], encoding_in, 'WX')
        prayoga_wx = self.xcode(args['prayoga'], encoding_in, 'WX')
        o = self.cached_api({'api' : 'verb_forms_api', 
            'root' : root_wx, 'prayoga' : prayoga_wx}, out_encoding)
        if 'result' not in o:
            return {'status' : 'Error: could not generate verb forms of root {}'.format(args['root'])}

        res = o['result']

        for parm in ['padi', 'lakara', 'purusha', 'vachana']:
            if parm in args and args[parm] != '':
                v = self.xcode(args[parm], encoding_in, 'Itrans')
                #print "in verb_forms: ", v
                v = self.presets.idx(parm, v)
                #print "in verb_forms: {} idx {}".format(parm, v)
                res = res[v]
                o[parm] = self.xcode(args[parm], encoding_in, out_encoding)
            else:
                o[parm] = [self.xcode(v, encoding_in, out_encoding) \
                    for v in self.presets.get(parm)]
                break

        o['in_encoding'] = encoding_in
        o['out_encoding'] = out_encoding
        #o['result'] = self.xcode(res, 'WX', out_encoding)
        o['result'] = res
        o['status'] = 'ok'
        if '_output' in o:
            del o['_output'] 
        if '_id' in o:
            del o['_id'] 
        return o

    def transform(self, inargs, outargs, out_encoding = None):
        if 'type' in outargs:
            inargs['type'] = outargs['type']
        res = self.analyze(inargs, 'Itrans')
        if 'status' in res and res['status'] != 'ok':
            return res
        #pprint(res)

        for f in ['encoding', 'linga']:
            if f in inargs and f not in outargs:
                outargs[f] = inargs[f]

        # Keep only those target word properties appropriate for transformation
        newargs = {a:outargs[a] for a in self.word_attrs if a in outargs}

        if not out_encoding:
            out_encoding = outargs['encoding']
        #print "transform args = ", newargs
        for a in res['result']:
            # Inherit all missing properties in outargs from analysis result
            if 'type' in newargs and a['type'] != newargs['type']:
                continue
                
            # Don't carry over the following properties as input to form gen
            excl_parms = []
            if a['type'] == 'subanta':
                excl_parms = ['vibhakti', 'vachana'] 
            elif a['type'] == 'ti~Nanta':
                excl_parms = ['lakara', 'purusha', 'vachana']
            for f in a:
                if f not in excl_parms and f not in newargs:
                    newargs[f] = a[f] 

            newargs['encoding'] = outargs['encoding']
            res = {'status' : 'Error: Unknown word type.'}
            if a['type'] == 'subanta':
                #newargs['root'] = a['root']
                #newargs['linga'] = a['linga']
                res = self.noun_forms(newargs, out_encoding)
            elif a['type'] == 'ti~Nanta':
                res = self.verb_forms(newargs, out_encoding)
            res['args'] = inargs
            res['in_encoding'] = inargs['encoding']
            #pprint(res)
            if '_output' in res:
                del res['_output'] 
            return res
            break

        return {'status' : 'Sorry, analysis returned no results.'}

if __name__ == "__main__":
    (cmddir, cmdname) = os.path.split(__file__)
    setmypath(os.path.abspath(cmddir))
    print "My path is " + mypath()
    initworkdir(True)

    v = grammar(True)
    #o = v.xcode(sys.argv[1], sys.argv[2], sys.argv[3])
    #print o

#    o = v.analyze({'word' : "gachChati", 'encoding' : "Itrans"}, \
#            out_encoding = 'Roman')
#    res = json.dumps(o, indent=4, ensure_ascii=False).encode('utf8')
#    print res

    o = v.transform(
        {'word' : "rAmeNa", 'encoding' : "Itrans", 'type' : 'subanta',
            'linga' : 'napuM',
        }, 
        {'vibhakti' : 2, }, out_encoding = 'Unicode')
    print json.dumps(o, indent=4, ensure_ascii=False).encode('utf-8')
    sys.exit(0)
#
#    o = v.transform(
#        {'word' : "gachChati", 'encoding' : "Itrans", 
#         'type' : 'ti~Nanta',
#        }, 
#        {'lakara' : 'laT', 'vachana' : 'bahu'}, out_encoding = 'Itrans')
#    print json.dumps(o, indent=4, ensure_ascii=False).encode('utf-8')
#
#    o = v.noun_forms({"root" : "rAma", "linga" : "puM", 
#            "encoding" : "Itrans", 
#            "vibhakti" : 6,
#            "vachana" : "bahu"
#            })
#    print json.dumps(o, indent=4, ensure_ascii=False).encode('utf-8')

    o = v.verb_forms(
        {'root' : "ak1", 'prayoga' : "kartari", 'encoding' : "Itrans",
         'padi' : 'parasmai', 'lakara' : 'la~N', 
         'purusha' : 'uttama'
        })
    print json.dumps(o, indent=4, ensure_ascii=False).encode('utf-8')

    o = v.verb_forms(
        {'root' : "ak1", 'prayoga' : "kartari", 'encoding' : "Itrans",
         'padi' : 'parasmai', 'lakara' : 'laT', 
         'purusha' : 'madhyama'
        })
    print json.dumps(o, indent=4, ensure_ascii=False).encode('utf-8')

    o = v.verb_forms(
        {'root' : "gam1", 'prayoga' : "kartari", 'encoding' : "Itrans",
         'padi' : 'parasmai', 'lakara' : 'laT', 
         'purusha' : 'prathama'
        })
    print json.dumps(o, indent=4, ensure_ascii=False).encode('utf-8')
    sys.exit(0)

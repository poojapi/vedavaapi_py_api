from config import *
import random
import sys,os
from mydb import *
from pprint import pprint
from grammar import grammar, purusha
from samvit import *
from resources.collections import *

class ParmGen:
    @staticmethod
    def permutations(options, start = 0, stop = 0):
        if stop == 0:
            stop = len(options)
        if start >= stop:
            yield []
            return
        #print "{}: start = {}, stop = {}".format(self.name, start, stop)
        vals = options[start] if hasattr(options[start], '__iter__') else [options[start]]
        for v in vals:
            #print (' ' * start) + str(v) + " ==> "
            if start+1 < stop:
                for x in ParmGen.permutations(options, start+1, stop):
                    yield [v] + x
            else:
                yield [v]
        return

    @staticmethod
    def gen_parmvals(parmvals):
        if isinstance(parmvals, dict):
            wlist = WordList(parmvals).get()
            #print "word list: "
            #pprint([v for v in wlist])
            return wlist
        elif isinstance(parmvals, list):
            return parmvals
        else:
            return [parmvals]

    @staticmethod
    def instances(parms):
        #print "parms = ", parms
        parm_names = parms.keys()
        pval_vectors = [ParmGen.gen_parmvals(parms[p]) for p in parm_names]
        #pprint(pval_vectors)
        
        for pval_vector in ParmGen.permutations(pval_vectors):
            pdict = dict(zip(parm_names, pval_vector))
            #pprint(pdict)
            yield pdict
        return

class WordList:
    def __init__(self, list_spec, name = '', attrs = {}):
        self.name = name
        self.collection = []
        if isinstance(list_spec, list):
            self.collection = list_spec
            self.attrs = attrs
            #self.collection = samvit().db().words.find({'word' : {'$in': f}})
        elif isinstance(list_spec, dict):
            for w in samvit().db()[list_spec['collection']] \
                    .find(list_spec['query']):
                if w:
                    w.update(attrs)
                    for p in w.keys():
                        if w[p] == '':
                            del w[p]
                    self.collection.append(w)

    def __str__(self):
        return "{} bank".format(self.name)

    def get(self):
        for elem in self.collection:
            for p in ParmGen.instances(elem):
                yield p
        return

def _subst_parms(parms, modifiers):
    #print "expand parms = ", parms
    #print "modifiers = ", modifiers
    newparms = parms.copy()
    for p,v in newparms.items():
        #print "p = ",p,"v = ",v
        if not re.search(r'\$\b', str(v)):
            continue
        try: 
            expr = re.sub(r'\$(\w+?)\b', r'modifiers["\1"]', v)
            newparms[p] = eval(expr)
        except Exception as e:
            print "Error: bad expression (ignoring):", expr, e
    for p,v in modifiers.items():
        if p not in newparms:
            newparms[p] = v
    #print "_subst_parms = ", newparms
    return newparms

def _xform(wdesc, modifiers):
    res = grammar().transform(wdesc, modifiers)
    if 'status' in res and res['status'] != 'ok':
        print "Error in _xform for "+str(wdesc['word'])+ ":", res['status']
        return None

    if 'result' in res:
        #print "{} -> {}".format(wdesc['word'], res['result'])
        return res['result']
    return None

class SktTemplate:
    def __init__(self, template):
        self.t = DotDict(template.copy())
        self.computed_components = []

    def __str__(self):
        return "<{}:\n    {}>".format(self.t.name,  \
            ",\n    ".join([str(c) for c in self.t.components]))

    def __repr__(self):
        return self.__str__()
        
    @staticmethod
    def _comp_instance(c, mod_parms):
        #print 'Component = ',c
        #print 'mod_parms = ', mod_parms
        if 'template' in c:
            t = samvit().db().templates.find_one({'name' : c['template']})
            #print "subtemplate = ", t
            if not t:
                return None
            template = SktTemplate(t)
            return template.instance(_subst_parms(c['parms'], mod_parms))
        elif 'word' in c:
            newparms = _subst_parms(c, mod_parms)
            if 'word' not in newparms:
                return None
            wdesc = newparms.copy()
            #{a:newparms[a] for a in ['word', 'encoding'] \
            #                if a in newparms}
            del newparms['word']
            if isinstance(wdesc['word'], dict):
                wdesc = wdesc['word']
            else:
                wdesc = { 'word' : wdesc['word'], 
                          'encoding' : wdesc['encoding'] }
            return _xform(wdesc, newparms)
        
    def _comp_instances(self, parm_dict):
        for c in self.t.components:
            val = SktTemplate._comp_instance(c, parm_dict)
            if not val:
                continue
            yield val

    def instance(self, parms, vaakya = ""):
        print "Parameters: "
        pprint(parms)
        if not vaakya:
            vaakya = self.t.vaakya
        cinstances = [c for c in self._comp_instances(parms)]
        if not cinstances:
            return ""

        print "Generated instances: "
        pprint(cinstances)
        for ind in range(len(cinstances)):
            val = cinstances[ind]
            val = val['word'] if isinstance(val, dict) else val
            vaakya = vaakya.replace('$'+str(ind+1), val)
        #print vaakya
        return vaakya

    def instances(self, parms, vaakya = ""):
        for pdict in ParmGen.instances(parms):
            #pprint(pdict)
            vaakya_desc = self.instance(pdict, vaakya)
            #print "Vaakya = " + str(vaakya)
            if not vaakya_desc:
                continue
            yield vaakya_desc

    @staticmethod
    def word_forms(wdesc, mod_parms):
        for pdict in ParmGen.instances(mod_parms):
            #pprint(pdict)
            newword = SktTemplate._comp_instance(wdesc, pdict)
            #print "Vaakya = " + str(vaakya)
            if not newword:
                continue
            yield newword

    @staticmethod
    def word_options(wdesc, all_opts, valid_opts):
        valid = [w for w in SktTemplate.word_forms(wdesc, valid_opts)]
        options = []
        for w in SktTemplate.word_forms(wdesc, all_opts):
            wopt = "=" + w if w in valid else "~" + w
            options.append(wopt)
        return options

if __name__ == "__main__":
    (cmddir, cmdname) = os.path.split(__file__)
    setmypath(os.path.abspath(cmddir))
    print "My path is " + mypath()
    initworkdir(True)

    grammar(True)
    samvit(True)
            
    visheshana_visheshya_template = {
        'samvit_levelid' : 1,
        'name' : 'visheShaNa-visheShya phrase', # Symbolic name
        'parms' : [ 'visheShaNa', 'visheShya', 'vibhakti', 'vachana' ], # Parameters to template
        'vaakya' : '$1 $2',
        'components' : [
            { 
                'word' : "$visheShaNa",
                'type': 'subanta', 'name' : 'visheShaNa'
            },
            { 
                'word' : "$visheShya",
                'type': 'subanta', 'name' : 'visheShya',
            }
        ]
    }
    samvit().db().templates.insert(visheshana_visheshya_template)

    karanam_kriya_template = {
        'samvit_levelid' : 2,
        'name' : 'karanam-kriya phrase',
        'parms' : [ 'karanam_pair', 'kriya_vachana', 'purusha', 'lakara' ],
        'vaakya' : '{=$1 ~$2}($3) $4',
        'components' : [
            { 
                'word' : "$karanam_pair['word1']",
                'type': 'subanta', 'name' : 'karanam', 'vibhakti' : 3,
            #    'vachana' : 'eka'
            },
            { 
                'word' : "$karanam_pair['word1']",
                'type': 'subanta', 'name' : 'karanam', 'vibhakti' : 6,
            #    'vachana' : 'eka'
            },
            { 
                'word' : "$karanam_pair['word1']",
                'type': 'subanta', 'name' : 'karanam', 'vibhakti' : 1,
                'vachana' : 'eka'
            },
            { 
                'word' : "$karanam_pair['word2']",
                'type': 'ti~Nanta', 'name' : 'kriya', 
                'vachana' : "$kriya_vachana",
                'lakara' : "$lakara",
                'purusha' : '$purusha'
            }
        ]
    }
    samvit().db().templates.insert(karanam_kriya_template)

    vaakyas = SktTemplate(karanam_kriya_template).instances(
        parms = {
            'karanam_pair' : { 
                'collection' : 'word_clusters', 
                'query' : {
                    'karaka' : 'karaNam', 
                    'source' : 'gita', 
                },
            },
            'kriya_vachana' : [ 'eka', 'bahu' ],
            'vibhakti' : 1,
            'encoding' : 'Itrans',
            'purusha' : 'uttama',
            'lakara' : 'lR^iT',
            'vachana' : 'bahu' })
    #for v in vaakyas:
    #    print v['word']
    #sys.exit(0)

    vaakyas = SktTemplate(visheshana_visheshya_template).instances(
        parms = {
            'visheShaNa' : {
                'collection' : 'words', 
                'query' : {
                    'context' : 'general', 
                    'subcontext' : 'parimANa' }
            },
            'visheShya' : [ 'rAmaH', 'kR^iShNaH' ],
            'vibhakti' : 7,
            'vachana' : 'bahu',
            'encoding' : 'Itrans'
            })
    for v in vaakyas:
        print " ".join(v)
    sys.exit(0)

    fourword_vaakya_template = {
        'samvit_levelid' : 3,
        'name' : 'fourword vaakya',
        'parms' : [ 'visheShaNa', 'visheShya', 'karanam_pair', 'vachana' ],
        'vaakya' : '$1 $2',
        'components' : [
            { 
                'template' : 'visheShaNa-visheShya phrase',
                'parms' : { 
                    'visheShaNa' : '$visheShaNa', 
                    'visheShya' : '$visheShya',
                    'vibhakti' : 1 
                }
            },
            {
                'template' : 'karanam-kriya phrase',
                'parms' : { 
                    'karanam_pair' : '$karanam_pair',
                    'kriya_vachana' : '$vachana',
                    'purusha' : "purusha($visheShya['word'], 'Itrans')",
                    'lakara' : 'laT',
                }
            }
        ]
    }
    samvit().db().templates.insert(fourword_vaakya_template)

    vaakyas = SktTemplate(fourword_vaakya_template).instances(
        parms = {
            'visheShaNa' : {
                'collection' : 'words', 
                'query' : {
                    'context' : 'general', 
                    'subcontext' : 'parimANa' }
            },
            #'visheShya' : [ 'rAmaH', 'kR^iShNaH' ],
            #'visheShaNa' : [ 'shikShakaH' ],
            'visheShya' : [ 
                { 'word' : 'kR^iShNaH', 'encoding' : 'Itrans' }, 
                { 'word' : 'tvam', 'linga' : 'puM', 'encoding' : 'Itrans' },
                { 'word' : 'aham', 'linga' : 'puM', 'encoding' : 'Itrans' } ],
            'karanam_pair' : [
#                { 'cluster' : 'vAhanam gachChati' },
#                { 'cluster' : 'mArjanI mArjayati' },
                { 'word1' : 'yAnam', 'word2' : 'gachChati' }],
            'vachana' : ['eka', 'bahu'],
            'encoding' : 'Itrans'
        })
    for v in vaakyas:
        print v

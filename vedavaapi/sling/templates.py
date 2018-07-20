from config import *
import random
import sys,os
from db.mydb import *
from pprint import pprint
from grammar import grammar
from samvit import *
from resources.collections import *

#visheShaNa_visheShya_template = {
#    'components' : [
#        {
#            'type' : 'subanta',
#        },
#        {
#            'type' : 'subanta',
#            'vibhakti' : { 'desc' : 0 },
#            'corpus' : { 'desc' : 0 }
#        }
#    ]
#}
#
#accompany_template = {
#    'components' : [
#        {
#            'type' : 'subanta',
#            'vibhakti' : 3
#        },
#        {
#            'type' : 'avyayam',
#            'corpus' : { 'list' : [ 'saha', 'vinaa' ] }
#        }
#    ]
#}
#
#tritiya_phrase_template = {
#    'components' : [
#        {
#            'type' : 'subanta',
#            'vibhakti' : 3,
#            'corpus' : { 'category' : 'tritiya_phrase' }
#        },
#        {
#            'type' : 'tinganta',
#            'corpus' : { 'category' : 'tritiya_phrase' }
#        }
#    ]
#}
#
#tritiya_vaakya_template = {
#    'components' : [
#        {
#            'type' : 'subanta',
#        }
#    ]
#}
#
#corpus = {
#    'name' : 'bhagavadgiita',
#    'fields' : ['pada', 'category'],
#    'values' : [] 
#}

class WordList:
    collection = []
    name = ""
    attrs = {}

    def __init__(self, name, f, attrs = {}):
        self.name = name
        if f and isinstance(f, list):
            self.collection = f
            self.attrs = attrs
            #self.collection = samvit().db().words.find({'word' : {'$in': f}})
        elif isinstance(f, dict):
            self.collection = [w for w in samvit().db().words.find(f)]

    def __str__(self):
        return "{} bank".format(self.name)

    def match(self, entry, attrs):
        return True
        for k, v in attrs.items():
            if not (k in entry and entry[k] == v):
                return False
        return True

    def sorted(self, query):
        return (w for w in sorted(self.collection) if self.match(w, query))

    def unique(self, query):
        return (d for d in self.collection if self.match(d, query))

    def rand(self, query):
        return (self.collection[i] \
            for i in random.shuffle(xrange(self.collection)) \
                if self.match(self.collection[i], query))

class SktTemplate:
    filters = {}
    name = ""
    def __init__(self, name, filters = {}):
        self.filters = filters
        self.name = name

    def __str__(self):
        return '{} template'.format(self.name)

    def __repr__(self):
        return self.__str__()

    def order(self):
        return ['unique', 'sorted', 'rand']

    def instances(self, attrs, order = 'sorted'):
        return None

class WordTemplate(SktTemplate):
    wordlist = None
    def __init__(self, name, wordlist, filters = {}):
        self.wordlist = wordlist
        SktTemplate.__init__(self, name, filters)

    def __str__(self):
        return '<{}: {}>'.format(SktTemplate.__str__(self), self.wordlist)

    def xform(self, w, modifiers):
        inattrs = { 'word' : w, 'encoding' : 'Itrans' }
        inattrs.update(self.wordlist.attrs)
        res = grammar().transform(inattrs, modifiers)
        if 'status' in res and res['status'] != 'ok':
            print "Error in WordTemplate.xform for "+w+ ":", res['status']
            return None

        if 'result' in res:
            print "{} -> {}".format(w, res['result'])
            return res['result']
        return None

    def instances(self, modifiers, order):
        #print "Instances called for ", self.name
        if not self.wordlist:
            return None
        newattrs = self.filters.copy()
        newattrs.update(modifiers)
        wordgen = None
        if order == 'unique':
            wordgen = self.wordlist.unique(newattrs)
        elif order == 'sorted':
            wordgen = self.wordlist.sorted(newattrs)
        elif order == 'rand':
            wordgen = self.wordlist.rand(newattrs)
        else:
            return None

        return filter(lambda x: x is not None, [self.xform(w, modifiers) for w in wordgen])

class PhraseTemplate(SktTemplate):
    components = []
    constraints = {}
    def __init__(self, name, filters = {}):
        self.components = []
        self.constraints = {}
        SktTemplate.__init__(self, name, filters)

    def __iadd__(self, component):
        if isinstance(component, list):
            self.components.extend(component)
        else: 
            self.components.append(component)
        return self

    def __str__(self):
        return "<{}:\n    {}>".format(SktTemplate.__str__(self),  \
            ",\n    ".join([str(c) for c in self.components]))

    def _permutations(self, options, start = 0, stop = 0):
        if stop == 0:
            stop = len(options)
        if start >= stop:
            yield []
            return
        #print "{}: start = {}, stop = {}".format(self.name, start, stop)
        for v in options[start]:
            #print (' ' * start) + v + " ==> "
            if start+1 < stop:
                for x in self._permutations(options, start+1, stop):
                    yield [v] + x
            else:
                yield [v]
        return

    def instances(self, attrs, order = 'sorted'):
        res_lists = [c.instances(attrs, order) for c in self.components]
        print "Phrase_template instances: "
        pprint(res_lists)
        return self._permutations(res_lists)

if __name__ == "__main__":
    (cmddir, cmdname) = os.path.split(__file__)
    setmypath(os.path.abspath(cmddir))
    print "My path is " + mypath()
    initworkdir(True)

    grammar(True)
    samvit_init()

    pronounbank = WordList('pronouns', ['eShaH', 'tasya'])
    visheshanabank = WordList('visheshaNas', ['sundaraH', 'nipuNaH', 'uttamaH'])
    nounbank = WordList('nouns', ['rAmaH', 'kR^iShNaH', 'govindaH'])
    verbbank = WordList('verbs', ['gachChati', 'paThati', 'likhati'], 
        {'type' : 'ti~Nanta'})

    pronountemplate = WordTemplate("sarvanaama", pronounbank, {'type' : 'subanta', 'kaaraka' : 'karanam' })
    print pronountemplate
    visheshanatemplate = WordTemplate("visheshana", visheshanabank, {'type' : 'subanta', 'kaaraka' : 'karanam' })
    nountemplate = WordTemplate("naama", nounbank, {'type' : 'subanta', 'kaaraka' : 'karanam' })
    verbtemplate = WordTemplate("verbs", verbbank, {'type' : 'ti~Nanta', 'kaaraka' : 'karanam' })

    visheShaNa_visheShya_template = PhraseTemplate("visheShaNa_visheShya")
    visheShaNa_visheShya_template += [
        pronountemplate,
        visheshanatemplate,
        nountemplate
      ]
    print visheShaNa_visheShya_template
    print "------------------------------------"

    tritiya_phrase_template = PhraseTemplate("karaNam")
    tritiya_phrase_template += [
        visheShaNa_visheShya_template,
        verbtemplate,
      ]
    print tritiya_phrase_template
    print "------------------------------------"
    #sys.exit(0)

    spec = {'linga' : 'puM', 'vibhakti' : 1, 'vachana' : 'bahu', 'lakara' : 'la~N' }
    pprint(spec)
    for vaakya in tritiya_phrase_template.instances(spec, order='sorted'):
        print "Vaakya = ",vaakya
        #print " ".join(vaakya)

#tritiya_phrase_template = {
#    'components' : [
#        {
#            'type' : 'subanta',
#            'vibhakti' : 3,
#            'corpus' : { 'category' : 'tritiya_phrase' }
#        }
#        {
#            'type' : 'tinganta',
#            'corpus' : { 'category' : 'tritiya_phrase' }
#        }
#    ]

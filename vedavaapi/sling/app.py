from sys import argv
import sys, getopt
from flask import Flask, Blueprint
from flask_restplus import Api
from ui import ui_bp
from grammar import *
from samvit_api import samvit_api
from samvit import *
import re

app = Flask(__name__)
api = Api(app)

api.add_resource(SktPresets, \
    '/presets', \
    '/presets/<field>')

api.add_resource(Dhaatus,  \
    '/dhaatus/schema',  \
    '/dhaatus',  \
    '/dhaatus/<_id>')

api.add_resource(SubantaRsrc, 
    '/samvit/subantas/schema', 
    '/samvit/subantas', 
    '/samvit/subantas/<_id>')
api.add_resource(WordClustersRsrc, 
    '/samvit/word_clusters/schema', 
    '/samvit/word_clusters', 
    '/samvit/word_clusters/<_id>')
api.add_resource(TemplatesRsrc, 
    '/samvit/templates/schema', 
    '/samvit/templates', 
    '/samvit/templates/<_id>')

app.register_blueprint(ui_bp, url_prefix='/ui')
app.register_blueprint(samvit_api, url_prefix='/samvit')

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/')
def index():
    return myresult([request.url + x \
        for x in ['presets', 'properties', 'xform', 'nounforms', 'verbforms', 'samvit']])

helpobj = {
    'properties' : {
        'args' : {
            'required' : ['word', 'encoding'],
            'optional' : ['out_encoding', '<presets> ...']
        },
        'desc' : {
            'word' : 'The word to be analyzed',
            'encoding' : 'Transliteration used for input parameters',
            'out_encoding' : 'Transliteration desired for output',
            'presets' : 'any of the preset grammar settings',
        },
        'output' : {
        }
    },
    'transform' : {
        'args' : {
            'required' : ['word', 'encoding', 'out_<presets>'],
            'optional' : ['out_encoding', '<presets> ...']
        },
        'desc' : {
            'word' : 'The word to be analyzed',
            'encoding' : 'Transliteration used for input parameters',
            'out_encoding' : 'Transliteration desired for output',
            'presets' : 'any of the preset grammatical attributes',
        },
        'output' : {
        }
    },
    'nounforms' : {
        'args' : {
            'required' : ['root', 'encoding', 'linga'],
            'optional' : ['out_encoding', 'vibhakti', 'vachana'],
        },
        'desc' : {
            'word' : 'The word to be analyzed',
            'encoding' : 'Transliteration used for input parameters',
            'out_encoding' : 'Transliteration desired for output',
            'presets' : 'any of the preset grammatical attributes'
        },
        'output' : {
        }
    },
    'verbforms' : {
        'args' : {
            'required' : ['root', 'encoding', 'prayoga'],
            'optional' : ['out_encoding', 'padi', 'lakara', 'purusha', 'vachana'],
        },
        'desc' : {
            'word' : 'The word to be analyzed',
            'encoding' : 'Transliteration used for input parameters',
            'out_encoding' : 'Transliteration desired for output',
        },
        'output' : {
        }
    },
    'transcode' : {
        'args' : {
            'required' : ['text', 'encoding', 'out_encoding'],
        },
        'desc' : {
            'text' : 'The text to be transliterated',
            'encoding' : 'Transliteration used for input text',
            'out_encoding' : 'Transliteration desired for output',
        },
        'output' : {
        }
    },
}

@app.route('/properties')
def properties():
    if not bool(request.args):
        return myresult(helpobj['properties'])
    #pprint(request.args)
    res = grammar().v().analyze(request.args)
    #pprint(res)
    return myresponse(res)

@app.route('/transform')
def transform():
    if not bool(request.args):
        return myresult(helpobj['transform'])
    inargs = dict((k ,v) for k, v in request.args.items() \
                if not re.match('^out_.*', k))
    #print "transform inargs: "
    #pprint(inargs)
    outargs = dict((re.sub('^out_', '', k) ,v) \
                    for k, v in request.args.items() \
                        if re.match('^out_.*', k))
    #print "transform outargs: "
    #pprint(outargs)
    res = grammar().v().transform(inargs, outargs)
    return myresponse(res)

@app.route('/nounforms')
def nounforms():
    if not bool(request.args):
        return myresult(helpobj['nounforms'])
    res = grammar().v().noun_forms(request.args)
    return myresponse(res)

@app.route('/verbforms')
def verbforms():
    if not bool(request.args):
        return myresult(helpobj['verbforms'])
    res = grammar().v().verb_forms(request.args)
    return myresponse(res)

@app.route('/transcode')
def transcode():
    if not bool(request.args):
        return myresult(helpobj['verbforms'])
    res = grammar().v().xcode_api(request.args)
    return myresponse(res)

(cmddir, cmdname) = os.path.split(__file__)
setmypath(os.path.abspath(cmddir))
print "My path is " + mypath()

parms = DotDict({
    'reset' : False,
    'dbreset' : False,
    'dbgFlag' : True,
    'myport' : PORTNUM,
    'localdir' : None,
    'wdir' : workdir(),
    })

def setup_app(parms):
    setworkdir(parms.wdir, parms.myport)
    print cmdname + ": Using " + workdir() + " as working directory."
    
    initworkdir(parms.reset)

    grammar(parms.dbreset)
    samvit(parms.dbreset)

    if parms.localdir:
        setwlocaldir(parms.localdir)
    if not path.exists(wlocaldir()):
        setwlocaldir(DATADIR_GRAMMAR)
    os.chdir(workdir())

def usage():
    print cmdname + " [-r] [-R] [-d] [-o <workdir>] [-l <local_wloads_dir>] <repodir1>[:<reponame>] ..."
    exit(1)

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "do:l:p:rRh", ["workdir="])
    except getopt.GetoptError:
        usage()

    global parms
    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ("-o", "--workdir"):
	        parms.wdir=arg
        elif opt in ("-l", "--localdir"):
            parms.localdir = arg
        elif opt in ("-p", "--port"):
            parms.myport = int(arg)
        elif opt in ("-r", "--reset"):
            parms.reset = True
        elif opt in ("-R", "--dbreset"):
            parms.dbreset = True
        elif opt in ("-d", "--debug"):
            parms.dbgFlag = True

    setup_app(parms)

    for a in args:
        components = a.split(':')
        if len(components) > 1:
            print "Importing " + components[0] + " as " + components[1]
            addrepo(components[0], components[1])
        else: 
            print "Importing " + components[0]
            addrepo(components[0], "")

    print "Available on the following URLs:"
    for line in mycheck_output(["/sbin/ifconfig"]).split("\n"):
        m = re.match('\s*inet addr:(.*?) .*', line)
        if m:
            print "    http://" + m.group(1) + ":" + str(parms.myport) + "/"
    app.run(
      host ="0.0.0.0",
      port = parms.myport,
      debug = parms.dbgFlag,
      use_reloader=False
     )

if __name__ == "__main__":
   main(sys.argv[1:])
else:
    setup_app(parms)

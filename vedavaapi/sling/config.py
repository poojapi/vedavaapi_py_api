import os
from os import path
from os.path import *
import re
import sys
import urllib2,getpass
import collections
import subprocess
from pprint import pprint
from json import dumps
from flask import *

PORTNUM = 9000
WORKDIR = "/tmp/vedavaapi_grammar"
DATADIR = "/opt/vedavaapi_grammar/data"
DATADIR_SETTINGS = join(DATADIR, "settings")
DATADIR_GRAMMAR = join(DATADIR, "grammar")
MYPATH = ""
LOG_LEVEL = 1

SERVER_CONFIG = {}

class DotDict(dict):
    def __getattr__(self, name):
        return self[name]

def mypath():
	return MYPATH

def serverconfig():
    global SERVER_CONFIG
    return SERVER_CONFIG

def setmypath(path):
	global MYPATH
	print "Setting my path to " + path
	MYPATH = path

def cmdpath(cmd):
	#print "Searching " + cmd + " in " + mypath()
	#return cmd
	return join(mypath(), cmd)

def setworkdir(arg,myport=PORTNUM):
    global WORKDIR
    wdir = join(arg,str(myport))
    print "Setting root working directory to " +wdir
    WORKDIR = wdir

def workdir():
    return WORKDIR

def pubsuffix():
    return "public"

def pubroot():
#    return join(workdir(), pubsuffix())
    return workdir()

def usersuffix(user):
    return join("users", user)

def userroot(user):
    return join(workdir(), usersuffix(user))

def pubdir(dir):
    return join(pubroot(), dir)

def repodir():
    return pubdir("grammar")

def wlocalprefix():
    return "local"

def wlocaldir():
    return join(repodir(), wlocalprefix())

def setwlocaldir(dir):
    print "Setting local store to " + dir
    addrepo(dir, wlocalprefix())

def uploaddir():
    return join(wlocaldir(), "upload")

def userpath(user, dir):
    return join(userroot(user), dir)

def loglevel():
    return LOG_LEVEL

def log(msg):
    if loglevel() > 0: print(msg)

def createdir(dir):
    if not path.exists(dir):
        print "Creating " + dir + " ..." 
        try:
            os.makedirs(dir, 0777)
        except Exception as e:
            print "Error: cannot create directory, aborting.\n",e
            sys.exit(1)

def initworkdir(reset):
    if (reset):
        print "Clearing previous contents of " + workdir()
        os.system("rm -rf " + workdir());

    print "Initializing work directory ..."
    createdir(workdir())
    createdir(pubroot())
#    createdir(workdir() + "/users")
    createdir(DATADIR_SETTINGS)
    cfgfile = join(DATADIR_SETTINGS, "server_config.json")
    if reset:
        print "Resetting server configuration to defaults"
        os.system("rm -f " + cfgfile)
    if not os.path.exists(cfgfile):
        cfgmaster = cmdpath("conf/server_config.json")
        if os.path.exists(cfgmaster):
            print "(Re-)initializing server configuration from", cfgmaster
            os.system("cp -a " + cfgmaster + " " + cfgfile)
    print "Loading server configuration from ", cfgfile
    with open(cfgfile, "r") as f:
        global SERVER_CONFIG
        SERVER_CONFIG = json.load(f)
    print "Server Configuration settings in effect: "
    print json.dumps(SERVER_CONFIG, indent=4)
    print "done."

def addrepo(d, reponame):
    if not isdir(d):
        return
    head, book = os.path.split(d)

    target = join(repodir(), reponame if reponame else book)
    createdir(dirname(target))
    if isdir(target) and not islink(target):
        print "Cannot create symlink: target " + target + " exists."
        return
    if exists(target):
        os.remove(target)
    cmd = "ln -s " + realpath(d) + " " + target
    os.system(cmd)

def convert(value):
    B=float(value)
    KB = float(1024)
    MB = float(KB ** 2)
    GB = float(KB ** 3)
    TB = float(KB ** 4)
    if(B < KB ):
        return '{0} {1}'.format(B,'Bytes' if 0== B>1 else 'B')
    if(KB <= B<MB):
        return '{0:.2f} KB'.format(B/KB)
    if(MB <= B<GB):
        return '{0:.2f} MB'.format(B/MB)
    if(GB <= B<TB):
        return '{0:.2f} GB'.format(B/GB)

def list_dirtree(rootdir):
    all_data = []
    try: 
        contents = os.listdir(rootdir)
    except Exception as e:
        print "Error listing "+rootdir+": ", e
        return all_data
    else:
        for item in contents:
            itempath = os.path.join(rootdir, item)
            info = {}
            children=[]
            if os.path.isdir(itempath):
                all_data.append( \
                    dict(title=item, \
                         path=itempath, \
                         folder=True, \
                         lazy=True, \
                         key=itempath))
            else:
                fsize = os.path.getsize(itempath)
                fsize = convert(fsize)
                fstr = '['+fsize+']'
                all_data.append(dict(title=item+' '+fstr,key=itempath))
    return all_data

def mycheck_output(cmd):
    try:
        #shellswitch = isinstance(cmd, collections.Sequence)
        #print "cmd:",cmd
        #print "type:",shellswitch
        shellval = False if (type(cmd) == type([])) else True
        return subprocess.Popen(cmd, shell=shellval, \
                stderr=subprocess.PIPE, \
                stdout=subprocess.PIPE).communicate()[0]
    except Exception as e:
        print "Error in ", cmd,": ", e
        return "error"

def array_to_utf(a):
    autf = []
    i = 0
    for v in a:
        if isinstance(v, unicode):
            autf.append(v.encode('utf-8'))
        elif isinstance(v, dict):
            autf.append(dict_to_utf(v))
        elif isinstance(v, list):
            autf.append(array_to_utf(v))
        else:
            autf.append(v)
    return autf

def dict_to_utf(d):
    dutf = {}
    for k,v in d.iteritems():
        if isinstance(v, unicode):
            dutf[k] = v.encode('utf-8')
        elif isinstance(v, list):
            dutf[k] = array_to_utf(v)
        elif isinstance(v, dict):
            dutf[k] = dict_to_utf(v)
        else:
            dutf[k] = v
    return dutf

def gen_response(status = 'ok', result = None):
    retobj = { 'status' : status }
    if not result is None:
        retobj['result'] = result
    resp = make_response(json.dumps(retobj, indent=4, ensure_ascii=False).encode('utf-8'))
    resp.headers['Content-Type'] = 'application/json'
    resp.headers['Charset'] = 'UTF-8'
    return resp
    #return json.dumps(retobj)
    
def myerror(msg):
    return gen_response(status = msg)

def myresponse(res = None):
    result = res['result'] if 'result' in res else None
    return gen_response(res['status'], result)
    
def myresult(res = None):
    return gen_response(result = res)

#function to check if an input url exists or not(for csv visualizer)
def check(url):
	try:
		urllib2.urlopen(url)
		return True
	except urllib2.HTTPError:
		return False

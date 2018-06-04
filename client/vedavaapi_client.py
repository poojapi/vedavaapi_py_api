import requests
from sys import argv
import sys, getopt
import os
import json
import sanskrit_data.schema.common as common_data_containers
from sanskrit_data.schema.users import *
from sanskrit_data.schema.ullekhanam import *

class DotDict(dict):
    def __getattr__(self, name):
        return self[name]

def print_dict(mydict):
    stext = json.dumps(mydict, indent=2, ensure_ascii=False, separators=(',', ': ')).encode('utf-8')
    print(stext)


Parms = DotDict({
    'reset' : False,
    'dbgFlag' : True,
    'server_baseurl' : '',
    'auth' : DotDict({'user' : 'vedavaapiAdmin', 'passwd' : '@utoDump1'}),
    'dbname' : ''
    })

(cmddir, cmdname) = os.path.split(__file__)

def invoke_api(session, op, url, parms = {}):
    print "op = {}, url = {}".format(op, url)
    url = Parms.server_baseurl + "/" + url
    try:
        if op == 'get':
            r = session.get(url, params=parms)
        elif op == 'post':
            print parms
            r = session.post(url, data=parms)
        elif op == 'delete':
            r = session.delete(url, data=parms)
        print(r.url)
        r.raise_for_status()
        return r
    except Exception as e:
        print("GET on {} returned {}".format(url, e))
        return None

def usage():
    print(cmdname + " [-r] [-u <userid>:<password>] [-d <dbname>] <server_baseurl> ...")
    exit(1)

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "rd:hu:", ["url="])
    except getopt.GetoptError:
        usage()

    global Parms
    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ("-r", "--reset"):
            Parms.reset = True
        elif opt in ("-u", "--auth"):
            Parms.auth = DotDict(dict(zip(('user', 'passwd'), arg.split(':'))))
            print Parms.auth
        elif opt in ("-d", "--db"):
            Parms.dbname = arg

    if not args:
        usage()
    Parms.server_baseurl = args[0]

    session = requests.Session()

    # First Authenticate with the Vedavaapi Server
    if Parms.auth.user:
        print "Authenticating to Vedavaapi with username {} and password {}".format(Parms.auth.user, Parms.auth.passwd)
        r = invoke_api(session, 'post', "auth/v1/password_login", {'user_id' : Parms.auth.user, 'user_secret': Parms.auth.passwd })
        if not r:
            print "Authentication failed; exiting."
            sys.exit(1)
    else:
        print "Proceeding without authentication ..."

    # Issue API calls
    if not Parms.dbname:
        print "Supply database to use via -d option."
        usage()
    r = invoke_api(session, 'get', "ullekhanam/v1/dbs/{}/books".format(Parms.dbname))
    if r:
        print_dict(r.json())
        books = common_data_containers.JsonObject.make_from_dict_list(r.json())
        print "retrieved {} ".format(len(books))
        #print_dict(user[0].to_json_map())

if __name__ == "__main__":
   main(sys.argv[1:])

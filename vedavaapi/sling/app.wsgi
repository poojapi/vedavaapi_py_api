import sys, os
import logging
from werkzeug.debug import DebuggedApplication

logging.basicConfig(stream=sys.stderr)

(mypath, fname) = os.path.split(__file__)
os.chdir(mypath)
print "My path is " + mypath
sys.path.insert (0, mypath)
sys.stdout = sys.stderr
from app import app
application = DebuggedApplication(app, True)

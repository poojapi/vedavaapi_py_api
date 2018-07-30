#!/usr/bin/python -u

"""
This is the main entry point. It does the following

-  starts the webservice (either as an independent flask server, or as an apache WSGI module)
-  sets up actions to be taken when various URL-s are accessed.
"""

# This web app may be run in two modes. See bottom of the file.

import getopt
# from flask.ext.cors import CORS
import logging
import os.path
import sys

from sanskrit_data.schema.common import JsonObject

# Add parent directory to PYTHONPATH, so that vedavaapi_py_api module can be found.
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from vedavaapi import common, ullekhanam
from sanskrit_data import file_helper
from vedavaapi.common.flask_helper import app

logging.basicConfig(
  level=logging.INFO,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

params = JsonObject()

params.set_from_dict({
  'debug': False,
  'port': 9000,
  'reset': False
})

def start_service(name):
    logging.info("Starting vedavaapi.{} service ...".format(name))
    svc_cls = "Vedavaapi" + str.capitalize(name)
    _tmp = __import__('vedavaapi.{}'.format(name), globals(), locals(), [svc_cls])
    svc_cls = eval('_tmp.'+svc_cls)
    svc_conf = common.server_config[name] if name in common.server_config else {}
    svc_obj = svc_cls(name, svc_conf)
    common.VedavaapiServices.register(name, svc_obj)

    if params.reset:
        logging.info("Resetting previous state of {} ...".format(name))
        svc_obj.reset()
    svc_obj.setup()
    svc_obj.register_api(app, "/{}".format(name))

def setup_app():
    common.set_configuration(config_file_name=os.path.join(os.path.dirname(__file__), 'conf_local/server_config.json'))

    services = ['store', 'users', 'ullekhanam']

    logging.info("Root path: " + app.root_path)
    for svc in services:
        start_service(svc)

def main(argv):
    def usage():
        logging.info("run.py [-d] [-r] [--port 4444]...")
        logging.info("run.py -h")
        exit(1)

    global params
    try:
        opts, args = getopt.getopt(argv, "drp:h", ["port=", "debug="])
        for opt, arg in opts:
            if opt == '-h':
                usage()
            if opt == '-r':
                params.reset = True
            elif opt in ("-p", "--port"):
                params.port = int(arg)
            elif opt in ("-d", "--debug"):
                params.debug = True
    except getopt.GetoptError:
        usage()

    setup_app()

    logging.info("Available on the following URLs:")
    for line in file_helper.run_command(["/sbin/ifconfig"]).split("\n"):
        import re
        m = re.match('\s*inet addr:(.*?) .*', line)
        if m:
            logging.info("    http://" + m.group(1) + ":" + str(params.port) + "/")
    app.run(
        host="0.0.0.0",
        port=params.port,
        debug=params.debug,
        use_reloader=False
    )


if __name__ == "__main__":
  logging.info("Running in stand-alone mode.")
  main(sys.argv[1:])
else:
  logging.info("Likely running as a WSGI app.")
  setup_app()

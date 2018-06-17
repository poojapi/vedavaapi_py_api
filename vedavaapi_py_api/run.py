#!/usr/bin/python3 -u

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

from vedavaapi_py_api import common, textract, ullekhanam
from sanskrit_data import file_helper
from vedavaapi_py_api.common.flask_helper import app

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


def setup_app():
  common.set_configuration(config_file_name=os.path.join(os.path.dirname(__file__), 'conf_local/server_config.json'))
  server_config = common.server_config

  client = None
  if server_config["db"]["db_type"] == "couchdb":
    from sanskrit_data.db.implementations import couchdb
    client = couchdb.CloudantApiClient(url=server_config["db"]["couchdb_host"])
  elif server_config["db"]["db_type"] == "mongo":
    from sanskrit_data.db.implementations import mongodb
    client = mongodb.Client(url=server_config["db"]["mongo_host"])

  if params.reset:
    print "Deleting database/collection", server_config["db"]["users_db_name"]
    client.delete_database(server_config["db"]["users_db_name"])
    for db_details in server_config["db"]["ullekhanam_dbs"]:
        print "Deleting database/collection", db_details["backend_id"]
        client.delete_database(db_details["backend_id"])
        if "file_store" in db_details:
            try:
                os.system("rm -rf " + db_details["file_store"])
            except Exception as e:
                logging.error("Error removing " + db_details["file_store"]+": "+ e)

  from vedavaapi_py_api import users
  users.setup(db=client.get_database_interface(db_name_backend=server_config["db"]["users_db_name"], db_name_frontend="users", db_type="users_db"), initial_users=server_config["initial_users"], default_permissions_in=server_config["default_permissions"])

  # Set up ullekhanam API databases.
  # ullekhanam is the main database/ service.
  from vedavaapi_py_api.ullekhanam.backend import add_db
  for db_details in server_config["db"]["ullekhanam_dbs"]:
    add_db(db=client.get_database_interface(db_name_backend=db_details["backend_id"],
    db_name_frontend=db_details["frontend_id"], external_file_store=db_details.get("file_store"), db_type="ullekhanam_db"), reimport=params.reset)

  logging.info("Root path: " + app.root_path)
  import vedavaapi_py_api.users.api_v1
  import vedavaapi_py_api.ullekhanam.api_v1
  import vedavaapi_py_api.textract.api_v1
  app.register_blueprint(users.api_v1.api_blueprint, url_prefix="/auth")
  app.register_blueprint(textract.api_v1.api_blueprint, url_prefix="/textract")
  app.register_blueprint(ullekhanam.api_v1.api_blueprint, url_prefix="/ullekhanam")

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

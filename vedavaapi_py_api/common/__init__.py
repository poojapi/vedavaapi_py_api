import json
import logging

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

server_config = None

def set_configuration():
  import os
  global server_config
  CODE_ROOT = os.path.dirname(os.path.dirname(__file__))
  config_file_name = os.path.join(CODE_ROOT, 'server_config_local.json')
  with open(config_file_name) as fhandle:
    server_config = json.loads(fhandle.read())
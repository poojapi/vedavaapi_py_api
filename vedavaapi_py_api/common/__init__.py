"""
Some common utilities.
"""

import json
import logging

logging.basicConfig(
  level=logging.INFO,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

"""Stores the server configuration."""
server_config = None


def set_configuration(config_file_name):
  """
  Reads the server configuration from the specified file, and stores it in the server_config module variable.
  :param config_file_name:
  :return:
  """
  global server_config
  with open(config_file_name) as fhandle:
    server_config = json.loads(fhandle.read())

"""
A general API to access and annotate a text corpus.

api_v1 is the main submodule.
"""

import logging

# Essential for depickling to work.
from sanskrit_data.schema import *  # pylint: disable=unused-import.

logging.basicConfig(
  level=logging.INFO,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

# Dummy usage.
logging.debug("So that depickling works well, we imported: " + str([common, ullekhanam, books, users]))

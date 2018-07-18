"""
A general API to access and annotate a text corpus.

api_v1 is the main submodule.
"""

import logging
import sys
import os

# Essential for depickling to work.

logging.basicConfig(
  level=logging.INFO,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

# Dummy usage.
#logging.debug("So that depickling works well, we imported: " + str([common, ullekhanam, books, users]))

from vedavaapi.common import *
#from grammar import grammar

class VedavaapiSling(VedavaapiService):
    def __init__(self, name, conf):
        super(VedavaapiSling, self).__init__(name, conf)
        self.vvstore = VedavaapiServices.lookup("store")
        
    def setup(self):
#        grammar(True)
        pass

    def reset(self):
        pass

from .api_v1 import api_blueprint as apiv1_blueprint

api_blueprints = [apiv1_blueprint]

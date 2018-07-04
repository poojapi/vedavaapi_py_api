"""
Intro
=====

This is a web-based tool (based on the ullekhanam module) to rapidly
decode scanned Indic document images into searchable text.

-  It will enable users to identify and annotate characters in scanned
   document images and auto-identifies similar characters.

"""

import logging
from vedavaapi.common import *

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class VedavaapiTextract(VedavaapiService):
    def __init__(self, name, conf):
        super(VedavaapiTextract, self).__init__(name, conf)
        self.vvstore = VedavaapiServices.lookup("store")

from api_v1 import api_blueprint as apiv1_blueprint

api_blueprints = [apiv1_blueprint]

"""
REST API
--------

Some general notes from the ullekhanam module apply. Additional API docs
`here`_ .

.. _here: http://api.vedavaapi.org/py/sling/docs
"""

from sys import argv
import sys, getopt
from flask import Blueprint, request
from flask_restplus import Api, Resource, reqparse
#from grammar import *
import re
import json
import logging
import os, sys
import traceback
from os.path import join

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from vedavaapi.sling import *
from .sandhi_join import SandhiJoiner

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

URL_PREFIX = '/v1'
api_blueprint = Blueprint(name='sling_api', import_name=__name__)
api = Api(app=api_blueprint, version='1.0', title='Vedavaapi SLING API',
                         description='Vedavaapi Samskrit Linguistics API. ',
                         prefix=URL_PREFIX, doc='/docs')

__all__ = ["api_blueprint"]

_sandhi_joiner = None
def sandhi_joiner():
    global _sandhi_joiner
    if not _sandhi_joiner:
        svc = VedavaapiServices.lookup("sling")
        _sandhi_joiner = SandhiJoiner(svc.config["scl_path"], svc.config["sandhi_gsheet_id"])
    return _sandhi_joiner

shakhas = [
        'sarva', 
        'Rigvediiya shaakala', 
        'yajurvedIya taittirIya', 
        'atharvavedIya shaunaka', 
        'sAmavedIya kauthuma', 
        'yajurvedIya mAdhyandina']

#api.add_resource(SktPresets, \
#    '/presets', \
#    '/presets/<field>')
#
#api.add_resource(Dhaatus,  \
#    '/dhaatus/schema',  \
#    '/dhaatus',  \
#    '/dhaatus/<_id>')

#api.add_resource(SubantaRsrc, 
#    '/samvit/subantas/schema', 
#    '/samvit/subantas', 
#    '/samvit/subantas/<_id>')
#api.add_resource(WordClustersRsrc, 
#    '/samvit/word_clusters/schema', 
#    '/samvit/word_clusters', 
#    '/samvit/word_clusters/<_id>')
#api.add_resource(TemplatesRsrc, 
#    '/samvit/templates/schema', 
#    '/samvit/templates', 
#    '/samvit/templates/<_id>')

#app.register_blueprint(samvit_api, url_prefix='/samvit')

@api.route('/sandhi/join')
class SandhiJoin(Resource):
  get_parser = api.parser()
  get_parser.add_argument('words', location='args', action='split', \
    required=True, type='string', help='give space-separated words to join!')
  get_parser.add_argument('encoding', location='args', required=True, \
        choices=['itrans', 'wx', 'slp1', 'devanagari'], \
        type='string', help='Give encoding used for words')
  get_parser.add_argument('shakha', location='args', type='string', \
        choices=shakhas)

  @api.expect(get_parser, validate=True)
  # Marshalling as below does not work.
  # @api.marshal_list_with(json_node_model)
  def get(self):
    """ Sandhi joiner
    
    :return: the samhita pada along with the sandhis applied.
    """
    args = request.args.to_dict()
    args['words'] = args['words'].replace(',', ' ').split()
    if 'shakha' not in args:
        args['shakha'] = '' 

    res = sandhi_joiner().join(args['words'], args['encoding'], shakha=args['shakha'])
    return res, 200

@api.route('/sandhi/refresh')
class SandhiRule(Resource):
  def get(self):
    """ Reload the Sandhi rulebase
    """
    return sandhi_joiner().reload(), 200

@api.route('/sandhi/rules')
class SandhiRule(Resource):
  get_parser = api.parser()
  get_parser.add_argument('shakha', location='args', type='string', \
        choices=shakhas,
        help='Show only rules that apply to this shaakha')
  def get(self):
    """ List existing sandhi rules
    """
    return sandhi_joiner().overrides, 200

@api.route('/sandhi/macros')
class SandhiRule(Resource):
  get_parser = api.parser()
  get_parser.add_argument('shakha', location='args', type='string', \
        choices=shakhas,
        help='Show only rules that apply to this shaakha')
  def get(self):
    """ List existing sandhi rules
    """
    return sandhi_joiner().macros, 200

#  @api.expect(post_parser, validate=True)
#  def post(self):
#    """ Add sandhi exception rule
#    """
#    form = request.form.to_dict()
#    global sandhi_overrides
#    if not form.keys():
#        sandhi_overrides = []
#    else:
#        sandhi_overrides.append(form)
#    return sandhi_overrides, 200

#helpobj = {
#    'properties' : {
#        'args' : {
#            'required' : ['word', 'encoding'],
#            'optional' : ['out_encoding', '<presets> ...']
#        },
#        'desc' : {
#            'word' : 'The word to be analyzed',
#            'encoding' : 'Transliteration used for input parameters',
#            'out_encoding' : 'Transliteration desired for output',
#            'presets' : 'any of the preset grammar settings',
#        },
#        'output' : {
#        }
#    },
#    'transform' : {
#        'args' : {
#            'required' : ['word', 'encoding', 'out_<presets>'],
#            'optional' : ['out_encoding', '<presets> ...']
#        },
#        'desc' : {
#            'word' : 'The word to be analyzed',
#            'encoding' : 'Transliteration used for input parameters',
#            'out_encoding' : 'Transliteration desired for output',
#            'presets' : 'any of the preset grammatical attributes',
#        },
#        'output' : {
#        }
#    },
#    'nounforms' : {
#        'args' : {
#            'required' : ['root', 'encoding', 'linga'],
#            'optional' : ['out_encoding', 'vibhakti', 'vachana'],
#        },
#        'desc' : {
#            'word' : 'The word to be analyzed',
#            'encoding' : 'Transliteration used for input parameters',
#            'out_encoding' : 'Transliteration desired for output',
#            'presets' : 'any of the preset grammatical attributes'
#        },
#        'output' : {
#        }
#    },
#    'verbforms' : {
#        'args' : {
#            'required' : ['root', 'encoding', 'prayoga'],
#            'optional' : ['out_encoding', 'padi', 'lakara', 'purusha', 'vachana'],
#        },
#        'desc' : {
#            'word' : 'The word to be analyzed',
#            'encoding' : 'Transliteration used for input parameters',
#            'out_encoding' : 'Transliteration desired for output',
#        },
#        'output' : {
#        }
#    },
#    'transcode' : {
#        'args' : {
#            'required' : ['text', 'encoding', 'out_encoding'],
#        },
#        'desc' : {
#            'text' : 'The text to be transliterated',
#            'encoding' : 'Transliteration used for input text',
#            'out_encoding' : 'Transliteration desired for output',
#        },
#        'output' : {
#        }
#    },
#}
#
#@api.route('/properties')
#class Properties(Resource):
#    def get(self):
#        if not bool(request.args):
#            return myresult(helpobj['properties'])
#        #pprint(request.args)
#        res = grammar().v().analyze(request.args)
#        #pprint(res)
#        return myresponse(res)
#
#@api.route('/transform')
#class Transform(Resource):
#    def get(self):
#        if not bool(request.args):
#            return myresult(helpobj['transform'])
#        inargs = dict((k ,v) for k, v in request.args.items() \
#                    if not re.match('^out_.*', k))
#        #print "transform inargs: "
#        #pprint(inargs)
#        outargs = dict((re.sub('^out_', '', k) ,v) \
#                        for k, v in request.args.items() \
#                            if re.match('^out_.*', k))
#        #print "transform outargs: "
#        #pprint(outargs)
#        res = grammar().v().transform(inargs, outargs)
#        return myresponse(res)
#
#@api.route('/nounforms')
#class Nounforms(Resource):
#    def get(self):
#        if not bool(request.args):
#            return myresult(helpobj['nounforms'])
#        res = grammar().v().noun_forms(request.args)
#        return myresponse(res)
#
#@api.route('/verbforms')
#class Verbforms(Resource):
#    def get(self):
#        if not bool(request.args):
#            return myresult(helpobj['verbforms'])
#        res = grammar().v().verb_forms(request.args)
#        return myresponse(res)
#
#@api.route('/transcode')
#class Transcode(Resource):
#    def get(self):
#        if not bool(request.args):
#            return myresult(helpobj['verbforms'])
#        res = grammar().v().xcode_api(request.args)
#        return myresponse(res)

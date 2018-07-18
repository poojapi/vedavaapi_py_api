"""
REST API
--------

See general notes from the ullekhanam module apply. Additional API docs
`here`_ .

.. _here: http://api.vedavaapi.org/py/textract/docs
"""

from sys import argv
import sys, getopt
from flask import Blueprint, request
from flask_restplus import Api, Resource, reqparse
from grammar import *
import re
import json
import logging
import os, sys
import traceback
from os.path import join

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

URL_PREFIX = '/v1'
api_blueprint = Blueprint(name='sling_api', import_name=__name__)
api = Api(app=api_blueprint, version='1.0', title='vedavaapi SLING API',
                         description='Vedavaapi SLING API. ',
                         prefix=URL_PREFIX, doc='/docs')

__all__ = ["api_blueprint"]

sandhi_rules = []

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
  get_parser.add_argument('words', location='args', action='split', required=True, type='string', help='give space-separated words!')
  get_parser.add_argument('encoding', location='args', required=True, \
        choices=['itrans', 'wx', 'slp1', 'devanagari'], \
        type='string', help='Give encoding used for words')
  get_parser.add_argument('shakha', location='args', type='string', \
        choices=['', 'Rik', 'krishna_yajus.madhyandina', 'shukla_yajus', 'saama', 'atharva'])

  @api.expect(get_parser, validate=True)
  # Marshalling as below does not work.
  # @api.marshal_list_with(json_node_model)
  def get(self):
    """ Sandhi joiner
    
    :return: the samhita pada
    """
    args = request.args.to_dict()
    args['words'] = args['words'].replace(',', ' ').split()
    if 'shakha' not in args:
        args['shakha'] = '' 

    from sandhi_join import sandhi_join
    res = sandhi_join(args['words'], args['encoding'], shakha=args['shakha'], exceptions=sandhi_rules)
    return res, 200

@api.route('/sandhi/rules')
class SandhiRule(Resource):
  def get(self):
    """ List existing sandhi rules
    """
    return sandhi_rules, 200

  post_parser = api.parser()
  post_parser.add_argument('shakha', location='args', type='string', \
        choices=['', 'Rik', 'krishna_yajus.madhyandina', 'shukla_yajus', 'saama', 'atharva'])
  post_parser.add_argument('priority', location='form', action='split', \
        type='int', choices=[1, 2, 3, 4, 5], \
        help='Relative priority of this rule')
  post_parser.add_argument('purva_pada', location='form', type='args', 
    help='give a regular expression for purva pada to match')
  post_parser.add_argument('uttara_pada', location='form', type='string', 
    help='give a regular expression for purva pada to match')
  post_parser.add_argument('samhita_pada', location='form', type='string', 
    help='give a regular expression for the final form')
  post_parser.add_argument('encoding', location='args', \
        choices=['itrans', 'wx', 'slp1', 'devanagari'], \
        type='string', help='Give encoding used for words')

  @api.expect(post_parser, validate=True)
  def post(self):
    """ Add sandhi exception rule
    """
    form = request.form.to_dict()
    global sandhi_rules
    if not form.keys():
        sandhi_rules = []
    else:
        sandhi_rules.append(form)
    return {}, 200

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

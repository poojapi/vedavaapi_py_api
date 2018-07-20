from config import *
from flask import Flask, Blueprint
from flask_restplus import Api, Resource

samvit_api = Blueprint('samvit_api', __name__)

@samvit_api.route('/')
def svindex():
    return myresult([request.url + x \
        for x in ['presets', 'templates']])


helpobj = {
    'properties' : {
        'args' : {
            'required' : ['word', 'encoding'],
            'optional' : ['out_encoding', '<presets> ...']
        },
        'desc' : {
            'word' : 'The word to be analyzed',
            'encoding' : 'Transliteration used for input parameters',
            'out_encoding' : 'Transliteration desired for output',
            'presets' : 'any of the preset grammar settings',
        },
        'output' : {
        }
    },
}

@samvit_api.route('/templates')
def templates():
    if not bool(request.args):
        return myresult(helpobj['properties'])
    #pprint(request.args)
    res = samvit.db().templates.find(request.args)
    #pprint(res)
    return myresponse(res)

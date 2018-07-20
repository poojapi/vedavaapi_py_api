from flask import Flask, Blueprint
from flask_restful import Api, Resource

ui_bp = Blueprint('ui_api', __name__)
ui_api = Api(ui_bp)

class TodoItem(Resource):
    def get(self, id):
        return {'task': 'Say "Hello, World!"'}

ui_api.add_resource(TodoItem, '/todos/<int:id>')

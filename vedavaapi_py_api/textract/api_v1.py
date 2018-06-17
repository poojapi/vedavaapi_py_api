"""
REST API
--------

See general notes from the ullekhanam module apply. Additional API docs
`here`_ .

.. _here: http://api.vedavaapi.org/py/textract/docs
"""

import copy
import json
import logging
import os, sys
import traceback
from os.path import join

import cv2
import flask_restplus
from sanskrit_data.schema import books
from sanskrit_data.schema import common as common_data_containers
from PIL import Image
from docimage import DocImage
from flask import Blueprint, request
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from vedavaapi_py_api.ullekhanam.api_v1 import BookList, get_user
from vedavaapi_py_api.ullekhanam.backend import get_db, get_file_store

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

URL_PREFIX = '/v1'
api_blueprint = Blueprint(name='textract_api', import_name=__name__)
api = flask_restplus.Api(app=api_blueprint, version='1.0', title='vedavaapi py API',
                         description='vedavaapi py API (Textract). '
                                     'For using some API, you need to log in using <a href="../auth/v1/oauth_login/google">google</a>.'
                                     'For a basic idea, see the <a href="../ullekhanam/docs">ullekhanam API docs</a>',
                         prefix=URL_PREFIX, doc='/docs')

# api = flask_restplus.Api(app, version='1.0', prefix=URL_PREFIX, title='vedavaapi py API',
#                          description='vedavaapi py API', doc= URL_PREFIX + '/docs/')



def is_extension_allowed(filename, allowed_extensions_with_dot):
  [fname, ext] = os.path.splitext(filename)
  return ext in allowed_extensions_with_dot


@api.route('/dbs/<string:db_id>/books')
@api.param('db_id', 'Hint: Get one from the JSON object returned by another GET call. ')
@api.doc(responses={
  200: 'Update success.',
  401: 'Unauthorized. Use <a href="../auth/v1/oauth_login/google">google</a> to login and request access at https://github.com/vedavaapi/vedavaapi_py_api .',
  405: "book with same ID already exists.",
  417: 'JSON schema validation error.',
  418: 'Illegal file extension.',
  419: 'Error saving page files.',
})
class ImageBookList(BookList):

  post_parser = api.parser()
  # The below only results in the ability to upload a single file from the SwaggerUI. TODO: Surpass this limitation.
  post_parser.add_argument('in_files', type=FileStorage, location='files')
  # post_parser.add_argument('jsonStr', location='json') would lead to an error - "flask_restplus.errors.SpecsError: Can't use formData and body at the same time"
  post_parser.add_argument('book_json', location='form', type='string')

  @api.expect(post_parser, validate=True)
  def post(self, db_id):
    """Handle uploading files.
    
    :return: Book details in a json tree like:
      {"content": BookPortionObj, "children": [JsonObjectNode with BookPortion_Pg1, JsonObjectNode with BookPortion_Pg2]}    
    """
    from vedavaapi_py_api import ullekhanam
    if not ullekhanam.api_v1.check_permission(db_name=db_id):
      return "", 401

    db = get_db(db_name_frontend=db_id)
    if db is None:
      return "No such db id", 404

    book_json = request.form.get("book_json")
    logging.debug(book_json)

    # To avoid having to do rollbacks, we try to prevalidate the data to the maximum extant possible.
    book = common_data_containers.JsonObject.make_from_pickledstring(book_json)
    if book.base_data != "image" or not isinstance(book, books.BookPortion) :
      message = {
        "message": "Only image books can be uploaded with this API."
      }
      return message, 417

    if hasattr(book, "_id"):
      message = {
        "message": "overwriting " + book._id + " is not allowed."
      }
      logging.warning(str(message))
      return message, 405

    # Check the files
    for uploaded_file in request.files.getlist("in_files"):
      input_filename = os.path.basename(uploaded_file.filename)
      allowed_extensions = {".jpg", ".png", ".gif"}
      if not is_extension_allowed(input_filename, allowed_extensions):
        message = {
          "message": "Only these extensions are allowed: %(exts)s, but filename is %(input_filename)s" % dict(exts=str(allowed_extensions), input_filename=input_filename) ,
        }
        logging.error(message)
        return message, 418

    # Book is validated here.
    book = book.update_collection(db_interface=db, user=get_user())

    try:
      page_index = -1
      for uploaded_file in request.files.getlist("in_files"):
        page_index = page_index + 1
        # TODO: Add image update subroutine and call that.
        page = books.BookPortion.from_details(
            title="pg_%000d" % page_index, base_data="image", portion_class="page",
            targets=[books.BookPositionTarget.from_details(position=page_index, container_id=book._id)]
          )
        page = page.update_collection(db_interface=db, user=get_user())
        page_storage_path = page.get_external_storage_path(db_interface=db)
        logging.debug(page_storage_path)

        input_filename = os.path.basename(uploaded_file.filename)
        logging.debug(input_filename)
        original_file_path = join(page_storage_path, "original__" + input_filename)
        if not os.path.exists(os.path.dirname(original_file_path)):
            os.makedirs(os.path.dirname(original_file_path))
        uploaded_file.save(original_file_path)

        image_file_name = "content.jpg"
        tmp_image = cv2.imread(original_file_path)
        cv2.imwrite(join(page_storage_path, image_file_name), tmp_image)

        image = Image.open(join(page_storage_path, image_file_name)).convert('RGB')
        working_filename = "content__resized_for_uniform_display.jpg"
        out = open(join(page_storage_path, working_filename), "w")
        img = DocImage.resize(image, (1920, 1080), False)
        img.save(out, "JPEG", quality=100)
        out.close()

        image = Image.open(join(page_storage_path, image_file_name)).convert('RGB')
        thumbnailname = "thumb.jpg"
        out = open(join(page_storage_path, thumbnailname), "w")
        img = DocImage.resize(image, (400, 400), True)
        img.save(out, "JPEG", quality=100)
        out.close()
    except:
      message = {
        "message": "Unexpected error while saving files: " + str(sys.exc_info()[0]),
        "deatils": traceback.format_exc()
      }
      logging.error(str(message))
      logging.error(traceback.format_exc())
      book_portion_node = common_data_containers.JsonObjectNode.from_details(content=book)
      logging.error("Rolling back and deleting the book!")
      book_portion_node.delete_in_collection(db_interface=db)
      return message, 419

    book_portion_node = common_data_containers.JsonObjectNode.from_details(content=book)
    book_portion_node.fill_descendents(db_interface=db)

    return book_portion_node.to_json_map(), 200


@api.route('/dbs/<string:db_id>/pages/<string:page_id>/image_annotations/all')
class AllPageAnnotationsHandler(flask_restplus.Resource):
  @api.doc(
    responses={404: 'id not found'})
  def get(self, page_id, db_id):
    """ Get all annotations (pre existing or automatically generated, using open CV) for this page.

    :param page_id:
    :param db_id
    :return: A list of JsonObjectNode-s with annotations with the following structure.
      {"content": ImageAnnotation, "children": [JsonObjectNode with TextAnnotation_1]}
    """
    logging.info("page get by id = " + str(page_id))
    db = get_db(db_name_frontend=db_id)
    if db is None:
      return "No such db id", 404
    page = common_data_containers.JsonObject.from_id(id=page_id, db_interface=db)
    if page is None:
      return "No such book portion id", 404
    else:
      page_image = DocImage.from_path(path=os.path.join(page.get_external_storage_path(db_interface=db), page.list_files(db_interface=db, suffix_pattern="content*")[0]))
      image_annotations = db.update_image_annotations(page=page, page_image=page_image)
      image_annotation_nodes = [common_data_containers.JsonObjectNode.from_details(content=annotation) for annotation in
                                image_annotations]
      for node in image_annotation_nodes:
        node.fill_descendents(db_interface=db)
      return common_data_containers.JsonObject.get_json_map_list(image_annotation_nodes), 200


@api_blueprint.route('/dirtree/<path:abspath>')
def listdirtree(abspath):
  """???."""
  # print abspath
  from sanskrit_data.file_helper import list_dirtree
  data = list_dirtree("/" + abspath)
  # logging.info("Data:" + str(json.dumps(data)))
  return json.dumps(data)

import copy
import json
import traceback
from os.path import join

import cv2
import flask_restplus
import os
import sanskrit_data.schema.books
import sanskrit_data.schema.common as common_data_containers
from PIL import Image
from docimage import DocImage
from flask import Blueprint, request
from vedavaapi_py_api.ullekhanam.api_v1 import BookList, EntityHandler
from vedavaapi_py_api.ullekhanam.backend import paths
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from vedavaapi_py_api.ullekhanam.backend.db import *

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

URL_PREFIX = '/v1'
api_blueprint = Blueprint(name='textract_api', import_name=__name__)
api = flask_restplus.Api(app=api_blueprint, version='1.0', title='vedavaapi py API',
                         description='vedavaapi py API (Textract). '
                                     'For a basic idea, see the <a href="../ullekhanam/docs">ullekhanam API docs</a>',
                         prefix=URL_PREFIX, doc='/docs')

# api = flask_restplus.Api(app, version='1.0', prefix=URL_PREFIX, title='vedavaapi py API',
#                          description='vedavaapi py API', doc= URL_PREFIX + '/docs/')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jp2', 'jpeg', 'gif'])

json_node_model = api.model('JsonObjectNode', common_data_containers.JsonObjectNode.schema)


@api.route('/books')
@api.doc(responses={
  200: 'Update success.',
  401: 'Unauthorized. Use /oauth/login/google to login and request access at https://github.com/vedavaapi/vedavaapi_py_api .',
  417: 'JSON schema validation error.',
})
class ImageBookList(BookList):
  @classmethod
  def allowed_file(cls, filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

  post_parser = api.parser()
  post_parser.add_argument('in_files', type=FileStorage, location='files')
  post_parser.add_argument('uploadpath', location='form', type='string')
  post_parser.add_argument('title', location='form', type='string')
  post_parser.add_argument('author', location='form', type='string')

  @api.expect(post_parser, validate=True)
  def post(self):
    """Handle uploading files.
    
    :return: Book details in a json tree like:
      {"content": BookPortionObj, "children": [JsonObjectNode with BookPortion_Pg1, JsonObjectNode with BookPortion_Pg2]}    
    """
    from vedavaapi_py_api import ullekhanam
    if not ullekhanam.api_v1.check_permission():
      return "", 401
    form = request.form
    logging.info("uploading " + str(form))
    bookpath = (form.get('uploadpath')).replace(" ", "_")

    abspath = join(paths.DATADIR, bookpath)
    logging.info("uploading to " + abspath)
    try:
      from vedavaapi_py_api.ullekhanam.backend.paths import createdir
      createdir(abspath)
    except Exception as e:
      logging.error(str(e))
      return "Couldn't create upload directory: %s , %s" % (format(abspath), str(e)), 500

    bookpath = abspath.replace(paths.DATADIR + "/", "")

    book = (sanskrit_data.schema.books.BookPortion.from_path(path=bookpath, db_interface=get_db()) or
            sanskrit_data.schema.books.BookPortion.from_details(path=bookpath, title=form.get("title"), base_data="image", portion_class="book"))

    if not book.authors: book.authors = [form.get("author")]

    pages = []
    page_index = -1
    for upload in request.files.getlist("file"):
      page_index = page_index + 1
      filename = upload.filename.rsplit("/")[0]
      if self.__class__.allowed_file(filename):
        filename = secure_filename(filename)
      destination = join(abspath, filename)
      upload.save(destination)
      [fname, ext] = os.path.splitext(filename)
      newFileName = fname + ".jpg"
      tmpImage = cv2.imread(destination)
      cv2.imwrite(join(abspath, newFileName), tmpImage)

      image = Image.open(join(abspath, newFileName)).convert('RGB')
      workingFilename = os.path.splitext(filename)[0] + "_working.jpg"
      out = open(join(abspath, workingFilename), "w")
      img = DocImage.resize(image, (1920, 1080), False)
      img.save(out, "JPEG", quality=100)
      out.close()

      image = Image.open(join(abspath, newFileName)).convert('RGB')
      thumbnailname = os.path.splitext(filename)[0] + "_thumb.jpg"
      out = open(join(abspath, thumbnailname), "w")
      img = DocImage.resize(image, (400, 400), True)
      img.save(out, "JPEG", quality=100)
      out.close()

      page = common_data_containers.JsonObjectNode.from_details(
        content=sanskrit_data.schema.books.BookPortion.from_details(
          title="pg_%000d" % page_index, path=os.path.join(book.path, newFileName), base_data="image", portion_class="page",
          targets=[sanskrit_data.schema.books.BookPositionTarget.from_details(position=page_index)]
        ))
      pages.append(page)

    book_portion_node = common_data_containers.JsonObjectNode.from_details(content=book, children=pages)

    book_portion_node_minus_id = copy.deepcopy(book_portion_node)
    book_portion_node_minus_id.content._id = None
    book_mfile = join(abspath, "book_v2.json")
    book_portion_node_minus_id.dump_to_file(book_mfile)

    try:
      book_portion_node.update_collection(get_db())
    except Exception as e:
      logging.error(format(e))
      traceback.print_exc()
      return format(e), 500

    return book_portion_node.to_json_map(), 200


@api.route('/books/<string:id>')
class ImageBookHandler(EntityHandler):
  pass

@api.route('/pages/<string:page_id>/image_annotations/all')
class AllPageAnnotationsHandler(flask_restplus.Resource):
  @api.doc(responses={404: 'id not found'})
  def get(self, page_id):
    """ Get all annotations (pre existing or automatically generated from open CV) for this page.
    
    :param page_id: 
    :return: A list of JsonObjectNode-s with annotations with the following structure.
      {"content": ImageAnnotation, "children": [JsonObjectNode with TextAnnotation_1]}    
    """
    logging.info("page get by id = " + str(page_id))
    book_portions_collection = get_db()
    page = common_data_containers.JsonObject.from_id(id=page_id, db_interface=book_portions_collection)
    if page == None:
      return "No such book portion id", 404
    else:
      image_annotations = get_db().update_image_annotations(page)
      image_annotation_nodes = [common_data_containers.JsonObjectNode.from_details(content=annotation) for annotation in
                                image_annotations]
      for node in image_annotation_nodes:
        node.fill_descendents(db_interface=get_db())
      return common_data_containers.JsonObject.get_json_map_list(image_annotation_nodes), 200


@api_blueprint.route('/relpath/<path:relpath>')
def send_file_relpath(relpath):
  """Get some data file - such as a page image."""
  from flask import send_from_directory
  return send_from_directory(paths.DATADIR, relpath)


# @app.route('/<path:abspath>')
# def details_dir(abspath):
#	logging.info("abspath:" + str(abspath))
#	return render_template("fancytree.html", abspath='/'+abspath)

@api_blueprint.route('/dirtree/<path:abspath>')
def listdirtree(abspath):
  """???."""
  # print abspath
  from vedavaapi_py_api.common.file_helper import list_dirtree
  data = list_dirtree("/" + abspath)
  # logging.info("Data:" + str(json.dumps(data)))
  return json.dumps(data)
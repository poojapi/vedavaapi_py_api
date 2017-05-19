import copy
import traceback
from os.path import join

import flask
import jsonpickle

import flask_restplus
from flask_login import current_user
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

import common.data_containers as common_data_containers
import backend.data_containers as backend_data_containers
from backend.collections import *
from backend.db import get_db
from backend.paths import createdir
from common import *

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

URL_PREFIX = '/v1'
api_blueprint = Blueprint(name='textract_api', import_name=__name__)
api = flask_restplus.Api(app=api_blueprint, version='1.0', title='vedavaapi py API', description='vedavaapi py API',
                         prefix=URL_PREFIX, doc='/docs')

# api = flask_restplus.Api(app, version='1.0', prefix=URL_PREFIX, title='vedavaapi py API',
#                          description='vedavaapi py API', doc= URL_PREFIX + '/docs/')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jp2', 'jpeg', 'gif'])


json_node_model = api.model('JsonObjectNode', data_containers.JsonObjectNode.schema)


@api.route('/books')
class BookList(flask_restplus.Resource):

  # Marshalling as below does not work.
  # @api.marshal_list_with(json_node_model)
  def get(self):
    """ Get booklist.
    
    :return: a list of JsonObjectNode json-s.
    """
    # TODO: does not return uploaded books as of May 19 2017.
    logging.info("Session in books_api=" + str(session['logstatus']))
    pattern = request.args.get('pattern')
    logging.info("books list filter = " + str(pattern))
    booklist = get_db().books.list_books(pattern)
    logging.debug(booklist)
    return data_containers.JsonObject.get_json_map_list(booklist), 200

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
    
    Form should be a json like: {?}
    TODO: Update booklist.
    """
    form = request.form
    logging.info("uploading " + str(form))
    bookpath = (form.get('uploadpath')).replace(" ", "_")

    abspath = join(paths.DATADIR, bookpath)
    logging.info("uploading to " + abspath)
    try:
      createdir(abspath)
    except Exception as e:
      logging.error(str(e))
      return "Couldn't create upload directory: %s , %s" % (format(abspath), str(e)), 500

    if current_user is None:
      user_id = None
    else:
      user_id = current_user.get_id()

    logging.info("User Id: " + str(user_id))
    bookpath = abspath.replace(paths.DATADIR + "/", "")

    book = (backend_data_containers.BookPortion.from_path(path=bookpath, collection= get_db().books.db_collection) or
            backend_data_containers.BookPortion.from_details(path=bookpath, title=form.get("title")))

    if (not book.authors): book.authors = [form.get("author")]

    pages = []
    page_index = -1
    for upload in request.files.getlist("file"):
      page_index = page_index + 1
      filename = upload.filename.rsplit("/")[0]
      if file and self.__class__.allowed_file(filename):
        filename = secure_filename(filename)
      destination = join(abspath, filename)
      upload.save(destination)
      [fname, ext] = os.path.splitext(filename)
      newFileName = fname + ".jpg"
      tmpImage = cv2.imread(destination)
      cv2.imwrite(join(abspath, newFileName), tmpImage)

      image = Image.open(join(abspath, newFileName)).convert('RGB')
      workingFilename = os.path.splitext(filename)[0] + "_working.jpg"
      out = file(join(abspath, workingFilename), "w")
      img = DocImage.resize(image, (1920, 1080), False)
      img.save(out, "JPEG", quality=100)
      out.close()

      image = Image.open(join(abspath, newFileName)).convert('RGB')
      thumbnailname = os.path.splitext(filename)[0] + "_thumb.jpg"
      out = file(join(abspath, thumbnailname), "w")
      img = DocImage.resize(image, (400, 400), True)
      img.save(out, "JPEG", quality=100)
      out.close()

      page = common_data_containers.JsonObjectNode.from_details(
        content=backend_data_containers.BookPortion.from_details(
          title = "pg_%000d" % page_index, path=os.path.join(book.path, newFileName)))
      pages.append(page)

    book_portion_node = common_data_containers.JsonObjectNode.from_details(content=book, children=pages)

    book_portion_node_minus_id = copy.deepcopy(book_portion_node)
    book_portion_node_minus_id.content._id = None
    book_mfile = join(abspath, "book_v2.json")
    book_portion_node_minus_id.dump_to_file(book_mfile)

    try:
      book_portion_node.update_collection(get_db().books.db_collection)
    except Exception as e:
      logging.error(format(e))
      traceback.print_exc()
      return format(e), 500

    return book_portion_node.to_json_map_via_pickle(), 200


@api.route('/books/<string:book_id>')
class BookPortionHandler(flask_restplus.Resource):
  def get(self, book_id):
    logging.info("book get by id = " + str(book_id))
    book_portions_collection = get_db().books.db_collection
    book_portion = common_data_containers.JsonObject.from_id(id=book_id, collection=book_portions_collection)
    if book_portion == None:
      return "No such book portion id", 404
    else:
      book_node = common_data_containers.JsonObjectNode.from_details(content=book_portion)
      book_node.fill_descendents(some_collection=book_portions_collection)
      # pprint(binfo)
      return book_node.to_json_map_via_pickle(), 200



@api.route('/pages/<string:page_id>/image_annotations/all')
class AllPageAnnotationsHandler(flask_restplus.Resource):
  def get(self, page_id):
    logging.info("page get by id = " + str(page_id))
    book_portions_collection = get_db().books.db_collection
    page = data_containers.JsonObject.from_id(id=page_id, collection=book_portions_collection)
    if page == None:
      return "No such book portion id", 404
    else:
      image_annotations = get_db().annotations.update_image_annotations(page)
      image_annotation_nodes = [data_containers.JsonObjectNode.from_details(content=annotation) for annotation in image_annotations]
      for node in image_annotation_nodes:
        node.fill_descendents(some_collection=get_db().annotations.db_collection)
      return data_containers.JsonObject.get_json_map_list(image_annotation_nodes), 200


@api.route('/pages/<string:page_id>/image_annotations')
class PageAnnotationsHandler(flask_restplus.Resource):
  def post(self, page_id):
    nodes = jsonpickle.loads( request.form['data'])
    # logging.info(jsonpickle.dumps(nodes))
    for node in nodes:
      node.update_collection(some_collection=get_db().annotations.db_collection)
    return data_containers.JsonObject.get_json_map_list(nodes), 200

  def delete(self, page_id):
    nodes = jsonpickle.loads( request.form['data'])
    for node in nodes:
      node.fill_descendents(some_collection=get_db().annotations.db_collection)
      node.delete_in_collection(some_collection=get_db().annotations.db_collection)
    return {}, 200



@api_blueprint.route('/relpath/<path:relpath>')
def send_file_relpath(relpath):
  return (send_from_directory(paths.DATADIR, relpath))


# @app.route('/<path:abspath>')
# def details_dir(abspath):
#	logging.info("abspath:" + str(abspath))
#	return render_template("fancytree.html", abspath='/'+abspath)

@api_blueprint.route('/dirtree/<path:abspath>')
def listdirtree(abspath):
  # print abspath
  data = list_dirtree("/" + abspath)
  # logging.info("Data:" + str(json.dumps(data)))
  return json.dumps(data)


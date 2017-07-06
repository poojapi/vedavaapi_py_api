import pymongo
import re
from bson.objectid import ObjectId

import common.data_containers
from common.db import DbInterface
from common.file_helper import *
from textract.docimage import *

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

logging.info("pymongo version is " + pymongo.__version__)


# Encapsulates the book_portions collection.
class BookPortionsInterface(DbInterface):
  def list_books(self, pattern=None):
    iter = self.get_no_target_entities()
    matches = [b for b in iter if not pattern or re.search(pattern, b.path)]
    return matches

  def get(self, path):
    book = data_containers.BookPortion.from_path(path=path, db_interface=self)
    book_node = common.data_containers.JsonObjectNode.from_details(content=book)
    book_node.fill_descendents(self)
    return book_node


# Encapsulates the annotations collection.
class AnnotationsInterface(DbInterface):
  def update_image_annotations(self, page):
    """return the page annotation with id = anno_id"""
    from os import path
    from textract.backend import paths
    page_image = DocImage.from_path(path=path.join(paths.DATADIR, page.path))
    known_annotations = page.get_targetting_entities(db_interface=self,
                                                     entity_type=data_containers.ImageAnnotation.get_wire_typeid())
    if len(known_annotations):
      logging.warning("Annotations exist. Not detecting and merging.")
      return known_annotations
      # # TODO: fix the below and get segments.
      # #
      # # # Give me all the non-overlapping user-touched segments in this page.
      # for annotation in known_annotations:
      #   target = annotation.targets[0]
      #   if annotation.source.type == 'human':
      #     target['score'] = float(1.0)  # Set the max score for user-identified segments
      #   # Prevent image matcher from changing user-identified segments
      #   known_annotation_targets.insert(target)

    # Create segments taking into account known_segments
    detected_regions = page_image.find_text_regions()
    logging.info("Matches = " + str(detected_regions))

    new_annotations = []
    for region in detected_regions:
      del region.score
      target = data_containers.ImageTarget.from_details(container_id=page._id, rectangle=region)
      annotation = data_containers.ImageAnnotation.from_details(
        targets=[target], source=data_containers.AnnotationSource.from_details(source_type='system_inferred', id="pyCV2"))
      annotation = annotation.update_collection(self)
      new_annotations.append(annotation)
    return new_annotations
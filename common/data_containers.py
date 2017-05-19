import logging

import flask
import jsonpickle
import jsonschema
from bson import json_util, ObjectId
from pymongo import ReturnDocument

import common
from textract import backend

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

TYPE_FIELD = "py/object"


class JsonObject(object):
  schema = {
    "type": "object",
    "properties": {
      TYPE_FIELD: {
        "type": "string"
      },
    },
    "required": [TYPE_FIELD]
  }

  def __init__(self):
    self.set_type()

  @classmethod
  def make_from_dict(cls, input_dict):
    assert input_dict.has_key(TYPE_FIELD), "no type field: " + str(input_dict)
    dict_without_id = input_dict
    _id = dict_without_id.pop("_id", None)
    # logging.debug(json_util.dumps(dict_without_id))
    obj = jsonpickle.decode(json_util.dumps(dict_without_id))
    # logging.debug(obj.__class__)
    if _id:
      obj._id = str(_id)
    obj.set_type_recursively()
    # logging.debug(obj)
    return obj

  @classmethod
  def make_from_pickledstring(cls, pickle):
    obj = jsonpickle.decode(pickle)
    return obj

  @classmethod
  def read_from_file(cls, filename):
    try:
      with open(filename) as fhandle:
        obj = jsonpickle.decode(fhandle.read())
        return obj
    except Exception as e:
      return logging.error("Error reading " + filename + " : ".format(e))
      raise e

  def dump_to_file(self, filename):
    try:
      with open(filename, "w") as f:
        f.write(str(self))
    except Exception as e:
      return logging.error("Error writing " + filename + " : ".format(e))
      raise e

  @classmethod
  def get_wire_typeid(cls):
    return cls.__module__ + "." + cls.__name__

  @classmethod
  def get_json_map_list(cls, some_list):
    return [item.to_json_map_via_pickle() for item in some_list]

  def set_type(self):
    # self.class_type = str(self.__class__.__name__)
    setattr(self, TYPE_FIELD, self.__class__.get_wire_typeid())
    # setattr(self, TYPE_FIELD, self.__class__.__name__)

  def set_type_recursively(self):
    self.set_type()
    for key, value in self.__dict__.iteritems():
      if isinstance(value, JsonObject):
        value.set_type_recursively()
      elif isinstance(value, list):
        for item in value:
          if isinstance(item, JsonObject):
            item.set_type_recursively()

  def __str__(self):
    return jsonpickle.encode(self)

  def set_from_dict(self, input_dict):
    if input_dict:
      for key, value in input_dict.iteritems():
        if isinstance(value, list):
          setattr(self, key, [JsonObject.make_from_dict(item) if isinstance(item, dict) else item for item in value])
        elif isinstance(value, dict):
          setattr(self, key, JsonObject.make_from_dict(value))
        else:
          setattr(self, key, value)

  def set_from_id(self, collection, id):
    return self.set_from_dict(
      collection.find_one({"_id": ObjectId(id)}))

  def to_json_map_via_pickle(self):
    return json_util.loads(jsonpickle.encode(self))

  def to_json_map(self):
    jsonMap = {}
    for key, value in self.__dict__.iteritems():
      if isinstance(value, JsonObject):
        jsonMap[key] = value.to_json_map()
      elif isinstance(value, list):
        jsonMap[key] = [item.to_json_map() if isinstance(item, JsonObject) else item for item in value]
      else:
        jsonMap[key] = value
    return jsonMap

  def equals_ignore_id(self, other):
    # Makes a unicode copy.
    def to_unicode(input):
      if isinstance(input, dict):
        return {key: to_unicode(value) for key, value in input.iteritems()}
      elif isinstance(input, list):
        return [to_unicode(element) for element in input]
      elif common.check_class(input, [str, unicode]):
        return input.encode('utf-8')
      else:
        return input

    dict1 = to_unicode(self.to_json_map())
    dict1.pop("_id", None)
    # logging.debug(self.__dict__)
    # logging.debug(dict1)
    dict2 = to_unicode(other.to_json_map())
    dict2.pop("_id", None)
    # logging.debug(other.__dict__)
    # logging.debug(dict2)
    return dict1 == dict2

  def update_collection(self, some_collection):
    self.set_type_recursively()
    if hasattr(self, "schema"):
      self.validate_schema()

    map_to_write = self.to_json_map()
    if hasattr(self, "_id"):
      filter = {"_id": ObjectId(self._id)}
      map_to_write.pop("_id", None)
    else:
      filter = self.to_json_map()

    updated_doc = some_collection.find_one_and_update(filter, {"$set": map_to_write}, upsert=True,
                                                      return_document=ReturnDocument.AFTER)
    self.set_type()
    updated_doc[TYPE_FIELD] = getattr(self, TYPE_FIELD)
    return JsonObject.make_from_dict(updated_doc)

  # To delete referrent items also, use appropriate method in JsonObjectNode.
  def delete_in_collection(self, some_collection):
    assert hasattr(self, "_id"), "_id not present!"
    return some_collection.delete_one({"_id": ObjectId(self._id)})

  def validate_schema(self):
    json_map = self.to_json_map()
    json_map.pop("_id", None)
    # logging.debug(str(self))
    # logging.debug(jsonpickle.dumps(self.schema))
    jsonschema.validate(json_map, self.schema)

  @classmethod
  def find_one(cls, filter, some_collection):
    attr_dict = some_collection.find_one(filter=filter)
    obj = None
    if attr_dict:
      obj = cls.make_from_dict(attr_dict)
    return obj

  @classmethod
  def find(cls, filter, some_collection):
    iter = some_collection.find(filter=filter)
    return [cls.make_from_dict(x) for x in iter]

  @classmethod
  def from_id(cls, id, collection):
    item = JsonObject.find_one(filter={"_id": ObjectId(id)}, some_collection=collection)
    return item

  def get_targetting_entities(self, some_collection, entity_type=None):
    filter = {
      "targets":  {
        "$elemMatch": {
          "container_id" : str(self._id)
        }
      }
    }
    if entity_type:
      filter[TYPE_FIELD] = entity_type
    targetting_objs = [JsonObject.make_from_dict(item) for item in some_collection.find(filter)]
    return targetting_objs


class JsonObjectNode(JsonObject):
  schema = common.recursively_merge(
    JsonObject.schema, {
      "properties": {
        "content": {
          "type": JsonObject.schema
        },
        "children": {
          "type": "array",
          "items": JsonObject.schema
        }
      },
      "required": [TYPE_FIELD]
    }
  )

  @classmethod
  def from_details(cls, content, children=None):
    if children is None:
      children = []
    node = JsonObjectNode()
    # logging.debug(content)
    # Strangely, without the backend.data_containers, the below test failed on 20170501
    assert isinstance(content, common.data_containers.JsonObject), content.__class__
    node.content = content
    # logging.debug(common.check_list_item_types(children, [JsonObjectNode]))
    assert common.check_list_item_types(children, [JsonObjectNode])
    node.children = children
    return node

  def update_collection(self, some_collection):
    self.content = self.content.update_collection(some_collection)
    for child in self.children:
      child.content.targets = [Target.from_details(str(self.content._id))]
      child.update_collection(some_collection)

  def delete_in_collection(self, some_collection):
    self.content.delete_in_collection(some_collection)
    id = str(self.content._id)
    for child in self.children:
      assert id in child.content.targets, "%d not in %s" % (id, str(child.content.targets))
      if hasattr(child.content, "_id"):
        child.content.targets.remove(id)
        if len(child.content.targets) > 0:
          child.content.update_collection(some_collection)
        else:
          child.delete_in_collection(some_collection)

  def fill_descendents(self, some_collection):
    targetting_objs = self.content.get_targetting_entities(some_collection=some_collection)
    self.children = []
    for targetting_obj in targetting_objs:
      child = JsonObjectNode.from_details(content=targetting_obj)
      child.fill_descendents(some_collection=some_collection)
      self.children.append(child)


class User(JsonObject):
    def __init__(self, user_id, nickname="Guest", email=None, confirmed_on=False):
        self.user_id = user_id
        self.nickname = nickname
        self.email = email
        self.confirmed_on = confirmed_on

    def is_authenticated(self):
        if self.nickname == 'Guest' and self.confirmed_on == True:
            logging.info("Confirmed=" + str( self.confirmed_on))
            return True

    def is_active(self):
        if self.confirmed_on == True:
            return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.user_id


class Target(JsonObject):
  schema = common.recursively_merge(JsonObject.schema, {
    "type": "object",
    "properties": {
      "container_id": {
        "type": "string"
      }
    },
    "required": ["container_id"]
  })

  @classmethod
  def from_details(cls, container_id):
    target = Target()
    target.container_id = container_id
    return target

  @classmethod
  def from_ids(cls, container_ids):
    target = Target()
    return [Target.from_details(str(container_id)) for container_id in container_ids]

  @classmethod
  def from_containers(cls, containers):
    return Target.from_ids(container_ids=[container._id for container in containers])
import json
import logging
from copy import deepcopy

import jsonpickle
import jsonschema
import sys

import common

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

TYPE_FIELD = "py/object"


def check_class(obj, allowed_types):
  results = [isinstance(obj, some_type) for some_type in allowed_types]
  # logging.debug(results)
  return (True in results)


def check_list_item_types(some_list, allowed_types):
  check_class_results = [check_class(item, allowed_types=allowed_types) for item in some_list]
  # logging.debug(check_class_results)
  return not (False in check_class_results)


def recursively_merge(a, b):
  assert a.__class__ == b.__class__, str(a.__class__) + " vs " + str(b.__class__)

  if isinstance(b, dict) and isinstance(a, dict):
    a_and_b = a.viewkeys() & b.viewkeys()
    every_key = a.viewkeys() | b.viewkeys()
    return {k: recursively_merge(a[k], b[k]) if k in a_and_b else
    deepcopy(a[k] if k in a else b[k]) for k in every_key}
  elif isinstance(b, list) and isinstance(a, list):
    return list(set(a + b))
  else:
    return b
  return deepcopy(b)


class JsonObject(object):
  schema = {
    "type": "object",
    "properties": {
      TYPE_FIELD: {
        "type": "string",
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
    # logging.debug(json.dumps(dict_without_id))
    new_obj = jsonpickle.decode(json.dumps(dict_without_id))
    # logging.debug(new_obj.__class__)
    if _id:
      new_obj._id = str(_id)
    new_obj.set_type_recursively()
    return new_obj

  @classmethod
  def make_from_dict_list(cls, input_dict_list):
    return [cls.make_from_dict(input_dict=input_dict) for input_dict in input_dict_list]

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

  def set_from_id(self, db_interface, id):
    return self.set_from_dict(db_interface.find_by_id(id=id))

  def to_json_map_via_pickle(self):
    return json.loads(jsonpickle.encode(self))

  def to_json_map(self):
    jsonMap = {}
    for key, value in self.__dict__.iteritems():
      # logging.debug("%s %s", key, value)
      if isinstance(value, JsonObject):
        jsonMap[key] = value.to_json_map()
      elif isinstance(value, list):
        jsonMap[key] = [item.to_json_map() if isinstance(item, JsonObject) else item for item in value]
      else:
        jsonMap[key] = value
    jsonMap[TYPE_FIELD] = self.__class__.get_wire_typeid()
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

  def update_collection(self, db_interface):
    if hasattr(self, "schema"):
      self.validate(db_interface)
    return db_interface.update_doc(self)

  # To delete referrent items also, use appropriate method in JsonObjectNode.
  def delete_in_collection(self, db_interface):
    return db_interface.delete_doc(self)

  def validate(self, db_interface=None):
    """
    
    :param db_interface: Potentially useful in subclasses to perfrom validations (eg. is the target_id valid).
    This value may not be availabe: for example when called from the from_details methods.
    :return: 
    """
    self.validate_schema()

  # Override and call this method to add extra validations.
  def validate_schema(self):
    json_map = self.to_json_map()
    json_map.pop("_id", None)
    # logging.debug(str(self))
    # logging.debug(jsonpickle.dumps(self.schema))
    from jsonschema import ValidationError
    from jsonschema import SchemaError
    try:
      jsonschema.validate(json_map, self.schema)
    except SchemaError as e:
      logging.error(jsonpickle.dumps(self.schema))
      raise e
    except ValidationError as e:
      logging.error(self)
      logging.error(self.schema)
      logging.error(json_map)
      raise e

  @classmethod
  def find_one(cls, filter, db_interface):
    """Returns None if nothing is found."""
    attr_dict = db_interface.find_one(filter=filter)
    obj = None
    if attr_dict:
      obj = cls.make_from_dict(attr_dict)
    return obj

  @classmethod
  def from_id(cls, id, db_interface):
    """Returns None if nothing is found."""
    item_dict = db_interface.find_by_id(id=id)
    item = None
    if item_dict != None:
      item = cls.make_from_dict(item_dict)
    return item

  def get_targetting_entities(self, db_interface, entity_type=None):
    return db_interface.get_targetting_entities(self, entity_type=entity_type)


class TargetValidationError(Exception):
  def __init__(self, allowed_types, target_obj, targetting_obj):
    self.allowed_types = allowed_types
    self.target_obj = target_obj
    self.targetting_obj = targetting_obj

  def __str__(self):
    return "%s\n targets object \n" \
           "%s,\n" \
           "which does not belong to \n" \
           "%s" % (self.targetting_obj, self.target_obj, str(self.allowed_types))


class Target(JsonObject):
  schema = recursively_merge(JsonObject.schema, {
    "type": "object",
    "properties": {
      TYPE_FIELD: {
        "enum": [__name__ + ".Target"]
      },
      "container_id": {
        "type": "string"
      }
    },
    "required": ["container_id"]
  })

  def get_target_entity(self, db_interface):
    """Returns null if db_interface doesnt have any such entity."""
    return JsonObject.from_id(id=self.container_id, db_interface=db_interface)

  @classmethod
  def from_details(cls, container_id):
    target = Target()
    target.container_id = container_id
    target.validate()
    return target

  @classmethod
  def from_ids(cls, container_ids):
    target = Target()
    return [Target.from_details(str(container_id)) for container_id in container_ids]

  @classmethod
  def from_containers(cls, containers):
    return Target.from_ids(container_ids=[container._id for container in containers])


class JsonObjectWithTarget(JsonObject):
  """A JsonObject with a target field."""

  schema = common.recursively_merge(JsonObject.schema, ({
    "type": "object",
    "description": "A JsonObject with a target field.",
    "properties": {
      "targets": {
        "type": "array",
        "items": Target.schema,
        "description": "This field lets us define a directed graph involving JsonObjects stored in a database."
      }
    }
  }))

  @classmethod
  def get_allowed_target_classes(cls):
    return []

  def validate_targets(self, targets, allowed_types, db_interface):
    if targets and len(targets) > 0 and db_interface != None:
      for target in targets:
        target_entity = target.get_target_entity(db_interface=db_interface)
        if not check_class(target_entity, allowed_types):
          raise TargetValidationError(allowed_types=allowed_types, targetting_obj=self, target_obj=target_entity)

  def validate(self, db_interface=None):
    super(JsonObjectWithTarget, self).validate(db_interface=db_interface)
    if hasattr(self, "targets"):
      self.validate_targets(targets=self.targets, allowed_types=self.get_allowed_target_classes(), db_interface=db_interface)


class JsonObjectNode(JsonObject):
  """Represents a tree (not a general Directed Acyclic Graph) of JsonObjectWithTargets."""
  schema = recursively_merge(
    JsonObject.schema, {
      "properties": {
        TYPE_FIELD: {
          "enum": [__name__ + ".JsonObjectNode"]
        },
        "content": JsonObject.schema,
        "children": {
          "type": "array",
          "items": JsonObjectWithTarget.schema
        }
      },
      "required": [TYPE_FIELD]
    }
  )

  def validate(self, db_interface=None):
    super(JsonObjectNode, self).validate(db_interface=None)
    for child in self.children:
      if not check_class(self.content, child.content.get_allowed_target_classes()):
        raise TargetValidationError(targetting_obj=child, target_obj=self.content)

    for child in self.children:
      child.validate(db_interface=None)


  @classmethod
  def from_details(cls, content, children=None):
    if children is None:
      children = []
    node = JsonObjectNode()
    # logging.debug(content)
    # Strangely, without the backend.data_containers, the below test failed on 20170501
    node.content = content
    # logging.debug(common.check_list_item_types(children, [JsonObjectNode]))
    node.children = children
    node.validate(db_interface=None)
    return node

  def update_collection(self, db_interface):
    self.validate(db_interface=db_interface)
    self.content = self.content.update_collection(db_interface)
    for child in self.children:
      child.content.targets = [Target.from_details(str(self.content._id))]
      child.update_collection(db_interface)

  def delete_in_collection(self, db_interface):
    self.fill_descendents(db_interface=db_interface, depth=100)
    for child in self.children:
      child.delete_in_collection(db_interface)
    # Delete or disconnect children before deleting oneself.
    self.content.delete_in_collection(db_interface)

  def fill_descendents(self, db_interface, depth=10):
    targetting_objs = self.content.get_targetting_entities(db_interface=db_interface)
    self.children = []
    if depth > 0:
      for targetting_obj in targetting_objs:
        child = JsonObjectNode.from_details(content=targetting_obj)
        child.fill_descendents(db_interface=db_interface, depth=depth-1)
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


class TextContent(JsonObject):
  schema = recursively_merge(JsonObject.schema, ({
    "type": "object",
    "properties": {
      TYPE_FIELD: {
        "enum": [__name__ + ".TextContent"]
      },
      "text": {
        "type": "string",
      },
      "language": {
        "type": "string",
      },
      "encoding": {
        "type": "string",
      },
    },
    "required": ["text"]
  }))

  @classmethod
  def from_details(cls, text, language="UNK", encoding="UNK"):
    text_content = TextContent()
    text_content.text = text
    text_content.language = language
    text_content.encoding = encoding
    text_content.validate()
    return text_content


def get_schemas(module_in):
  import inspect
  schemas = {}
  for name, obj in inspect.getmembers(module_in):
    if inspect.isclass(obj) and obj.schema:
      schemas[name] = obj.schema
  return schemas

import logging

from sanskrit_data.schema.users import User

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

users_db = None
default_permissions = None


def setup(db, initial_users=None, default_permissions_in=None):
  global users_db
  logging.info(db.__class__)
  users_db = db
  users_db.add_index(keys_dict={
    "authentication_infos.auth_user_id": 1
  }, index_name="authentication_infos.auth_user_id")

  # Add initial users to the users db if they don't exist.
  logging.info("Add initial users to the users db if they don't exist.")
  if initial_users is not None:
    for initial_user_dict in initial_users:
      initial_user = User.make_from_dict(initial_user_dict)
      matching_users = users_db.get_matching_users_by_auth_infos(user=initial_user)
      if len(matching_users) == 0:
        logging.info("Adding: " + str(initial_user))
        # Use this instead of update_doc to auto-generate auth_secret_bcrypt
        initial_user.update_collection(db_interface=users_db)
      else:
        logging.info("Not adding: " + str(initial_user))

  global default_permissions
  default_permissions = default_permissions_in


# Directly accessing the module variable seems to yield spurious None values.
def get_db():
  return users_db


def get_default_permissions():
  return default_permissions

from flask import url_for, session
from flask_oauthlib.client import OAuth
import logging
logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

from sanskrit_data.schema.users import User, UserPermission

class OAuthSignIn(object):
  """An interface to be extended for supporting various oauth authentication providers.

  A simple way to understand how this is used is to see how it is called from users_api_v1.py.  
  Important private members:
    provider_name
    service: An oauth.remote_app object, set in the subclass constructor.
  """

  providers = None

  def __init__(self, provider_name):
    self.provider_name = provider_name

  def authorize(self):
    """User-agent is directed to the oauth provider website, with a standard callback url."""
    callback_url = url_for('.authorized', provider=self.provider_name,
            _external=True)
    return self.service.authorize(callback_url)

  def authorized_response(self):
    return self.service.authorized_response()

  @classmethod
  def get_provider(cls, provider_name, ):
    """Get the appropriate subclass to handle login.
    
    Ensures that we use singletons.
    """
    import common
    oauth_config = common.server_config["oauth"]
    if cls.providers is None:
      cls.providers = {}
      for provider_class in cls.__subclasses__():
        provider = provider_class(client_id=oauth_config[provider_name]["client_id"], client_secret=oauth_config[provider_name]["client_secret"])
        cls.providers[provider.provider_name] = provider
    return cls.providers[provider_name]

  @staticmethod
  def get_token(token=None):
    """This method is passed as an argument to the oauth.remote_app object.
    """
    return session.get('oauth_token')

  def get_session_data(self, data):
    pass

  # Use oauth token in session to get userdata from the oauth service
  def get_user_data(self):
    return None

  # Construct or look up a User object using data obtained from get_user_data().
  def get_user(self):
    pass


class GoogleSignIn(OAuthSignIn):
  def __init__(self, client_id, client_secret):
    super(GoogleSignIn, self).__init__(provider_name="google")
    oauth = OAuth()
    self.service = oauth.remote_app(
      'google',
      consumer_key=client_id,
      consumer_secret=client_secret,
      request_token_params={
        'scope': 'email'
      },
      base_url='https://www.googleapis.com/oauth2/v1/',
      request_token_url=None,
      access_token_method='POST',
      access_token_url='https://accounts.google.com/o/oauth2/token',
      authorize_url='https://accounts.google.com/o/oauth2/auth',
    )
    self.service.tokengetter(GoogleSignIn.get_token)

  def get_session_data(self, data):
    return (
      data['access_token'],
      ''
    )

  def get_user_data(self):
    access_token = session.get('oauth_token')
    token = 'OAuth ' + access_token[0]
    headers = {b'Authorization': bytes(token.encode('utf-8'))}
    data = self.service.get(
      'https://www.googleapis.com/oauth2/v1/userinfo', None,
      headers=headers)
    return data.data

  def get_user(self):
    data = self.get_user_data()
    logging.debug(data)
    from common.db.users_db import users_db
    user = users_db.find_one(filter={"authentication_infos.auth_user_id": data['email'], "authentication_infos.auth_provider": self.provider_name})
    logging.debug(user)
    if user is None:
      user = User.from_details(nickname=data['name'], auth_user_id=data['email'], user_type="human", auth_provider=self.provider_name)
    if data['email'].replace("@", "___") == "vishvas.vasuki___gmail.com":
      user.permissions = [UserPermission.from_details(service=".*", actions=["read", "write", "admin"])]
    logging.debug(user)
    return user

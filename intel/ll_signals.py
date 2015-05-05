from django.contrib.auth.signals import user_logged_in
from request_provider.signals import get_request

import ll_logger
from ll_debug import __debugvar__

class SignalHandler:
  def __init__(self, logger):
    self.logger = logger

  # self = sender in this context, when looked from the perspective of the
  # Django signal system
  def login(self, user, request, **kwargs):
    self.logger.instance.addFilter(ll_logger.ContextFilter(request))
    msg = 'User({0}) logged in'.format(request.user.username)
    self.logger.info(self.logger.to_request('Login', msg))

  def logout(self, user, request, **kwargs):
    self.logger.instance.addFilter(ll_logger.ContextFilter(request))
    msg = 'User({0}) logged out'.format(request.user.username)
    self.logger.info(self.logger.to_request('Logout', msg))

  # Must override logged username from POST since user is not logged in
  def failed_login(self, credentials, **kwargs):
    request = get_request()
    username = request.POST.get('username', 'Undefined')
    self.logger.instance.addFilter(
      ll_logger.ContextFilter(request, overrides={'user':username})
    )
    msg = 'User({0}) failed login'.format(username)
    self.logger.info(self.logger.to_request('Login.fail', msg))

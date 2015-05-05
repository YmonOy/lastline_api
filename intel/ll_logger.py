import logging
import sys
import traceback
from ipware.ip import get_ip

from ll_debug import __debugvar__

# Responsible for adding context to syslog messages like ip and username
# Takes request, and a dict of overrides like: 'user':'someusername'
class ContextFilter(logging.Filter):
  def __init__(self, request, overrides={}):
    self.request = request
    self.overrides = overrides

  def filter(self, record):
    record.ip = get_ip(self.request)
    if(record.ip is None): record.ip = 'None' 

    if(self.request.user.is_authenticated()): record.user = self.request.user.username
    else: record.user = self.overrides.get('user', 'AnonymousUser')
    return True

class Logger:

  # eg.
  # log = Logger(level=logging.INFO)

  def __init__(self, **kwargs):

    if kwargs.get("level") is not None:
      level = kwargs["level"]
    else: level = logging.WARNING

    # Create a python logger
    self.instance = logging.getLogger('ll_logger')
    self.instance.setLevel(level)

    # Build log formatters
    logFormatter = logging.Formatter('%(levelname)s user(%(user)s) ip(%(ip)s) %(message)s')

    # Logs to syslog
    syslog = logging.handlers.SysLogHandler(address = '/dev/log')
    syslog.setLevel(level)
    syslog.setFormatter(logFormatter)
    self.instance.addHandler(syslog)

    # Expose logging API
    self.debug = self.instance.debug
    self.info = self.instance.info
    self.warning = self.instance.warning 
    self.error = self.instance.error
    self.critical = self.instance.critical
    self.exception = self.instance.exception

  # Returns the name of the function that called this function.
  def caller_name():
    return sys._getframe(1).f_code.co_name

  # Format internal log messages
  # Context can be 'self' if in class, otherwise string that will be displayed.
  def to_internal(self, context, msg, act='call'):
    context_str = context if isinstance(context, str) else context.__class__.__name__
    function = sys._getframe(1).f_code.co_name
    formatted = '{0}({1}.{2}): {3}'.format(
      act,
      context_str,
      function,
      msg
    )
    return formatted

  # Format request based log messages
  def to_request(self, context, msg, act='call'):
    if not isinstance(context, str): context = context.__class__.__name__
    formatted = '{0}({1}): {2}'.format(
      act,
      context,
      msg
    )
    return formatted

# Handling uncaught exceptions so that there is a log trace.
# Potential problems with multithreaded applications? 
def uncaught_exception_handler(ex_cls, ex, tb):
  # TODO: Needs proper formatting for logs. Do we have to call logger again?
  logger = Logger()
  logger.critical(''.join(traceback.format_tb(tb)))
  logger.critical('{0}: {1}'.format(ex_cls, ex))

# Decorator for exception catching and logging
# Can take arguments. Should be for the moment used in a class which defines:
# self.instance = logger
#
# Can be applied to any function inside a class error traces need to be logged from.
class LogExceptions(object):
  #def __init__(self, arg1, arg2, arg3):
  #  self.arg1 = arg1

  def __call__(self, func):
    # Can take only single argument, function object to be called.
    def wrapped_func(*args):
      logger = args[0].logger # Logger object gets passed as argument
                              # directly from the this.logger instance
                              # Could also be: getattr(self, attribute) ?

      try:
        # Run wrapped function here, return results all the way
        result = func(*args)
        return result
      except Exception, e:
        # Still uses a single logger instance and provides a proper traceback log :)
        logger.exception(logger.to_internal(self, 'Uncaught exception! Traceback as follows:'))
        raise
    return wrapped_func

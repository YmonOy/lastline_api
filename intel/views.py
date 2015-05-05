# Initialize logging
import logging
import sys
import ll_logger
logger = ll_logger.Logger(level=logging.INFO)
sys.excepthook = ll_logger.uncaught_exception_handler # Log all uncaught exceptions

from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.template import RequestContext, loader
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required # Currently only for index

import ll_connect
import ll_forms
from ll_mixins import LoginRequiredMixin 
from ll_debug import __debugvar__

import json

# Set up signal handling
import ll_signals
from django.contrib.auth import signals
signalhandler = ll_signals.SignalHandler(logger)
signals.user_logged_in.connect(signalhandler.login)
signals.user_logged_out.connect(signalhandler.logout)
signals.user_login_failed.connect(signalhandler.failed_login)

# Init connection and any other common data we need for views
def __doinit__():
  global logger
 
  api = ll_connect.APIConn(logger)
  config_parser = api.load_config()
  client = api.connect_api(config_parser)
  client.load_all_views()
  return({'logger': logger,
         'api': api,
         'config_parser': config_parser,
         'client': client})

def __formJsonError__(classref, form):
  # JS component expects errors to be wrapped with 'errors' tag.
  errors = '{{ "errors": [ {0} ] }}'.format(form.errors.as_json(escape_html=True))
  logger.error(logger.to_request(classref, errors))
  return errors

@login_required
def index(request):
  logger.instance.addFilter(ll_logger.ContextFilter(request))
  #template = loader.get_template("ajax.html")
  #return HttpResponse(template.render(context))
  context = {
    #'repr': repr(request),
  }
  return render(request, 'intel/index.html', context)


# All ajax/API calls should in the future support querying multiple sites.
# Extensibility, commanding multiple ll managers are goals here.

# Blacklist related views 

class List_ip(LoginRequiredMixin, View):

  def get(self, request):
    logger.instance.addFilter(ll_logger.ContextFilter(request))
    lastline = __doinit__()
    response = json.dumps(lastline['api'].ll_list_ip())
    logger.debug(logger.to_request(self, response)) 
    return HttpResponse(response, content_type='application/json')

class List_domain(LoginRequiredMixin, View):

  def get(self, request):
    logger.instance.addFilter(ll_logger.ContextFilter(request))
    lastline = __doinit__()
    response = json.dumps(lastline['client'].intel.list_domain())
    logger.debug(logger.to_request(self, response)) 
    return HttpResponse(response, content_type='application/json')

# Base blacklist class that all blacklist views extend
class BlacklistView(LoginRequiredMixin, View):
  form_class = ll_forms.Add_ipForm # Default

  def form_valid(self, form):
    # By default only give error
    return HttpResponseBadRequest('')

  def post(self, request, *args, **kwargs):
    logger.instance.addFilter(ll_logger.ContextFilter(request))
    form = self.form_class(request.POST) 
    if form.is_valid(): 
      logger.info(logger.to_request(self, json.dumps(form.cleaned_data['entries'])))
      response = self.form_valid(form) # Call classes form_valid()
      logger.info(logger.to_request(self, json.dumps(response), act='response'))
      return JsonResponse(response)
    else:
      return HttpResponse(__formJsonError__(self, form),
                          content_type='application/json') 

# Extends BlacklistView to add IP addresses
class Add_ip(BlacklistView):
  form_class = ll_forms.Add_ipForm

  def form_valid(self, form):
    lastline = __doinit__()
    # Note extra [] for list 
    return lastline['api'].ll_add_ip([form.cleaned_data['entries']])

# Extends BlacklistView to delete IP addresses
class Delete_ip(BlacklistView):
  form_class = ll_forms.Delete_ipForm

  def form_valid(self, form):
    lastline = __doinit__()
    return lastline['api'].ll_delete_ip(form.cleaned_data['entries'])

# Extends BlacklistView to add domains
class Add_domain(BlacklistView):
  form_class = ll_forms.Add_domainForm

  def form_valid(self, form):
    lastline = __doinit__()
    # Note extra [] for list 
    return lastline['api'].ll_add_domain([form.cleaned_data['entries']])

# Extends BlacklistView to delete domains
class Delete_domain(BlacklistView):
  form_class = ll_forms.Delete_domainForm

  def form_valid(self, form):
    lastline = __doinit__()
    # Note extra [] for list 
    return lastline['api'].ll_delete_domain(form.cleaned_data['entries'])

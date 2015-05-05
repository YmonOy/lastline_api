from django.contrib.auth.decorators import login_required

class LoginRequiredMixin(object):
  @classmethod
  def as_view(cls, **initkwargs):
    view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
    return login_required(view)

# Depracted, replaced by ipware and improved logging
class RequestParserMixin(object):
  @classmethod
  def parse_request(self, request):
    parsed = {}
    parsed['user'] = request.user.username \
      if request.user.is_authenticated() else 'Anonymous'
    parsed['ip'] = request.META.get('HTTP_X_FORWARDED_FOR','') \
      or request.META.get('REMOTE_ADDR','')
    return(parsed)

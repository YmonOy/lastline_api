from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import RedirectView

# For development only, static should be offered through httpd
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'lastline_api.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$', RedirectView.as_view(url='intel/')),
    url(r'^intel/', include('intel.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/$', 'django.contrib.auth.views.login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'})
)

# For development only, static should be offered through httpd
urlpatterns += staticfiles_urlpatterns()

# Rename admin site
admin.site.site_title = "Lastline_API admin"
admin.site.site_header = "Lastline_API administration"
admin.site.index_title = "Lastline_API administration"

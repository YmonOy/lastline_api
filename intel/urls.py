from django.conf.urls import patterns, url

# For development only
#from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from intel import views

urlpatterns = patterns('',
  url(r'^$', views.index, name='index'),
  url(r'^list_ip$', views.List_ip.as_view(), name='list_ip'),
  url(r'^list_domain$', views.List_domain.as_view(), name='list_domain'),
  url(r'^add_ip$', views.Add_ip.as_view(), name='add_ip'),
  url(r'^delete_ip$', views.Delete_ip.as_view(), name='delete_ip'),
  url(r'^add_domain$', views.Add_domain.as_view(), name='add_domain'),
  url(r'^delete_domain$', views.Delete_domain.as_view(), name='delete_domain'),
)

# For development only
#urlpatterns += staticfiles_urlpatterns()

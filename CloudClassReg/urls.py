from django.conf.urls import patterns, include, url
from django.contrib import admin, auth
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'CloudClassReg.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^reg/', include('registration.urls', namespace="reg")),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^admin/', include(admin.site.urls)),
)

from django.conf.urls import patterns, url

from registration import views

urlpatterns = patterns('',
    # ex: /polls/
    url(r'^$', views.index, name='index'),
    url(r'^cart/', views.cart, name='cart'),
    url(r'^emptycart/', views.empty_cart, name='empty_cart'),
    url(r'^removeitem/', views.remove_cart_item, name='remove_cart_item'),
    url(r'^catalog/', views.catalog, name='catalog'),
    url(r'^enroll/', views.enroll, name='enroll'),
    url(r'^sched/', views.sched, name='sched'),
    url(r'^oauth2callback/', views.auth_return, name='auth_return'),
    url(r'^logout/', views.logout_view, name='logout'),
)
from django.conf.urls import patterns, include, url
import rideshare.views

urlpatterns = patterns('',
    url(r'^$', rideshare.views.home), 
    url(r'^rides/$', rideshare.views.all_rides), 
    url(r'^rides/remove/([0-9]+)/$', rideshare.views.remove_from_ride), 
    url(r'^rides/add/([0-9]+)/$', rideshare.views.add_to_ride), 
    url(r'^rides/create/$', rideshare.views.create_ride), 
    url(r'^login/$', rideshare.views.authenticate), 
    url(r'^logout/$', rideshare.views.logout), 
    url(r'^forgot-password/$', rideshare.views.forgot_password), 
    url(r'^recover/([0-9]+)/$', rideshare.views.recover), 
    url(r'^verify/([0-9]+)/$', rideshare.views.home), 
    url(r'^rides/comments/([0-9]+)/$', rideshare.views.get_comments), 
    url(r'^rides/comments/add/([0-9]+)/$', rideshare.views.add_comment), 
    url(r'^users/add/$', rideshare.views.create_user), 
    url(r'^users/modify/$', rideshare.views.modify_user), 
    url(r'^search/$', rideshare.views.search), 
)

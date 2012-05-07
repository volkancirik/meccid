from django.conf.urls.defaults import *

#from meccid.settings import MEDIA_ROOT
from meccid.settings import MEDIA_ROOT

#from django.contrib.comments.models import Comment

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',

    (r'^main/([a-z]+)/([a-z]+)/(?P<pIndex>\d+)/(?P<direction>up|down|clear)vote/?$','meccid.blog.views.votePost' ),
#    (r'^main/filter/(?P<criteria>til|politics|self|other)/?$', 'meccid.blog.views.filterPost'),
#    (r'^main/(?P<criteria>date|pop|vote)/?$', 'meccid.blog.views.sort'),

    (r'^main/(?P<sort>date|pop|vote|recent)/(?P<filter>til|politics|self|other|all)/?$', 'meccid.blog.views.listAll'),
    (r'^main/', 'meccid.blog.views.main_view'),

#    (r'sample/','meccid.blog.views.sample'),
#    (r'sparql/','meccid.blog.views.sparql'),
#    (r'freebase/','meccid.blog.views.freeBase'),

    (r'^img/(?P<path>.*)$', 'django.views.static.serve',{'document_root': MEDIA_ROOT}),

    (r'^blog/page/(?P<page_id>\d+)/(?P<owner>\d+)/(?P<contributor>\d+)/$', 'meccid.blog.views.addTag'),
    (r'^blog/page/(?P<page_id>[^/]+)/$', 'meccid.blog.views.view_page'),
    (r'^blog/page/(?P<page_id>[^/]+)/(?P<tIndex>\d+)/(?P<direction>up|down|clear)vote/?$','meccid.blog.views.voteObject' ),
    (r'^blog/page/(?P<tIndex>\d+)/votescrtc/(?P<direction>up|down|clear)vote/?$','meccid.blog.views.voteObjectScr' ),
    (r'^blog/page/(?P<page_id>[^/]+)/(?P<tIndex>[^/]+)/$', 'meccid.blog.views.replyItem'),
    (r'^blog/userToUser/(?P<page_id>[^/]+)/(?P<author>[^/]+)/$', 'meccid.blog.views.updateUserToUser'),
    (r'^blog/page/(?P<pIndex>[^/]+)/vote/(?P<direction>up|down|clear)vote/?$','meccid.blog.views.votePost' ),
    (r'^blog/page/(?P<pIndex>[^/]+)/votescr/(?P<direction>up|down|clear)vote/?$','meccid.blog.views.votePostScr' ),

    (r'^admin/', admin.site.urls),
    (r'^comments/', include('django.contrib.comments.urls')),
    (r'^login/$', 'django.contrib.auth.views.login'),
#    (r'^tree/(?P<page_id>[^/]+)/$', 'meccid.blog.views.treePath'),
    (r'^profile/$', 'meccid.blog.views.profileView'),
    (r'^profile/(?P<uname>[^/]+)/$', 'meccid.blog.views.profileViewName'),
    (r'^logout/$', 'meccid.blog.views.logout_page'),
    (r'^register/', 'meccid.blog.views.registerUser'),
    (r'^new_post/$', 'meccid.blog.views.new_post'),
    (r'^new_post_save/$', 'meccid.blog.views.new_post_save'),
    (r'^export/$', 'meccid.blog.views.exportToFile'),
    (r'^updatet/$', 'meccid.blog.views.updateTagToTags'),
    url(r'^$', 'meccid.blog.views.main_view'), # Should be the last element.
)
from django.conf.urls import url

from . import views


urlpatterns = [
    # mute these after deployment
    url(r'^initialize/tecnum$', views.initialize_data, {'data': 'tec-num'}),

    # test functions
    url(r'^test/upload$', views.test_upload),
]

from django.conf import settings
from django.urls import path, re_path
from django.views.static import serve

from . import views

urlpatterns = [
    path('upload/', views.upload_zip, name='upload'),
    path('', views.home, name='home'),
    re_path(r'^asset/(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR / 'instacheck' / 'asset'}),
    re_path(r'^(?P<filename>.*\.html)$', views.serve_html, name='serve_html'),
]

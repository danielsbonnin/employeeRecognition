"""teamiota URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
# https://docs.djangoproject.com/en/1.10/topics/auth/default/#using-the-views
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
import teamiota.views
from . import settings
import logging
urlpatterns = [
    url(r'^$', teamiota.views.LoginView.as_view()),
    url('^password_reset/$',
        auth_views.password_reset,
        {
            'template_name': 'passwords/password_reset_form.html',
            'email_template_name': 'passwords/password_reset_email.txt',
            'subject_template_name': 'passwords/password_reset_subject.txt',
            'from_email': settings.DEFAULT_FROM_EMAIL,
        },
        name='password_reset'),
    url('^password_reset/done/$',
        auth_views.password_reset_done,
        {
            'template_name': 'passwords/password_reset_done.html',
        },
        name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm,
        {
            'template_name': 'passwords/password_reset_confirm.html',
        },
        name='password_reset_confirm'),
    url('^reset/done/$',
        auth_views.password_reset_complete,
        {
            'template_name': 'passwords/password_reset_complete.html',
        },
        name='password_reset_complete'),
    url(r'^teamiota/', include('teamiota.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^administrator/', include('administrator.urls')),
]
urlpatterns += static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

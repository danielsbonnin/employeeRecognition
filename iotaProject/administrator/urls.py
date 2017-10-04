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
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.admin_account, name='index'),
    url(r'logout/', views.logout_user, name='logout'),
    url(r'edit/', views.edit),
    url(r'add_user/', views.add_user),
    url(r'list/', views.list),
    url(r'delete/(?P<user_id>[0-9]+)$', views.delete),
    url(r'edit_user/(?P<user_id>[0-9]+)$', views.edit_user),
    url(r'reports/(?P<report_id>[1-9]+)$', views.reports),
    url(r'reports/custom/', views.reports_filter),
]

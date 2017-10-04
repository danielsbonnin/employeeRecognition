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
    url(r'^$', views.NormalUsersPortal.as_view(), name='normalUsersPortal'),
    url(r'^NormalUsersPortal/', views.NormalUsersPortal.as_view(), name='normalUsersPortal'),
    url(r'^login/', views.LoginView.as_view(), name='normalUserLogin'),
    url(r'^logout/', views.LogoutView.as_view(), name='normalUserLogout'),
    url(r'^award/(?P<pk>[0-9]+)/', views.AwardView.as_view(), name='awardView'),
    url(r'^revoke/', views.RevokeView.as_view(), name='revokeView'),
    url(r'^DrawnSigSubmitted/',
        views.DrawnSigSubmitted.as_view(),
        name='drawnSigSubmitted'),
]

"""remote_control URL Configuration

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
from django.contrib import admin
import control.views as control_views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', control_views.home),
    url(r'^control/$', control_views.control),
    url(r'^stream/$', control_views.stream),
    url(r'^car/$', control_views.car),
    url(r'^calibration/$', control_views.calibration),
    url(r'^connection_test/$', control_views.connection_test),
]

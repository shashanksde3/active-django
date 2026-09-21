from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("about/", TemplateView.as_view(template_name="core/about.html"), name="about"),
    path("services/", TemplateView.as_view(template_name="core/services.html"), name="services"),
    path("team/", TemplateView.as_view(template_name="core/team.html"), name="team"),
]

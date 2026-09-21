from django.http import HttpRequest, HttpResponse
from django.urls import include, path


def crash(request: HttpRequest) -> HttpResponse:
    raise RuntimeError("Simulated failure")


urlpatterns = [
    path("crash/", crash),
    path("", include("config.urls")),
]

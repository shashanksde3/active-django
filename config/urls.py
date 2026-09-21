from django.urls import include, path

urlpatterns = [
    path("", include("apps.core.urls")),
    path("portfolio/", include("apps.portfolio.urls")),
    path("blog/", include("apps.blog.urls")),
    path("", include("apps.contact.urls")),
]

from django.urls import path

from . import views

app_name = "portfolio"

urlpatterns = [
    path("", views.PortfolioItemListView.as_view(), name="list"),
    path("<slug:slug>/", views.PortfolioItemDetailView.as_view(), name="detail"),
]

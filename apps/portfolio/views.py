from typing import Any

from django.http import Http404
from django.views.generic import DetailView, ListView

from .content import Category, PortfolioItem, all_items, get_item


class PortfolioItemListView(ListView):
    template_name = "portfolio/item_list.html"
    context_object_name = "items"

    def get_queryset(self) -> tuple[PortfolioItem, ...]:
        return all_items()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.choices
        return context


class PortfolioItemDetailView(DetailView):
    template_name = "portfolio/item_detail.html"
    context_object_name = "item"

    def get_object(self, queryset: Any = None) -> PortfolioItem:
        item = get_item(self.kwargs["slug"])
        if item is None:
            raise Http404("No Portfolio Item matches the given slug.")
        return item

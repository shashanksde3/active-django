from typing import Any

from django.http import Http404
from django.views.generic import DetailView, ListView

from .content import BlogPost, all_posts, get_post

SIDEBAR_RECENT_POSTS = 5


class BlogPostListView(ListView):
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self) -> tuple[BlogPost, ...]:
        return all_posts()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if context["is_paginated"]:
            page = context["page_obj"]
            context["page_range"] = page.paginator.get_elided_page_range(page.number)
        return context


class BlogPostDetailView(DetailView):
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_object(self, queryset: Any = None) -> BlogPost:
        post = get_post(self.kwargs["slug"])
        if post is None:
            raise Http404("No Blog Post matches the given slug.")
        return post

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        others = [post for post in all_posts() if post != self.object]
        context["recent_posts"] = others[:SIDEBAR_RECENT_POSTS]
        return context

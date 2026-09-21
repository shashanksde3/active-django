from typing import Any

from django.views.generic import TemplateView

from apps.blog.content import all_posts

HOME_RECENT_POSTS = 3


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["recent_posts"] = all_posts()[:HOME_RECENT_POSTS]
        return context

from django import template

from apps.blog.content import BlogPost, all_posts

register = template.Library()

FOOTER_RECENT_POSTS = 2


@register.inclusion_tag("blog/partials/footer_recent_posts.html")
def footer_recent_posts() -> dict[str, tuple[BlogPost, ...]]:
    return {"posts": all_posts()[:FOOTER_RECENT_POSTS]}

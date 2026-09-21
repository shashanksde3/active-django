"""Callers use only all_posts(), get_post() and the fields, so a model can replace this module."""

from dataclasses import dataclass
from datetime import date
from operator import attrgetter

from django.urls import reverse


@dataclass(frozen=True, slots=True)
class Author:
    name: str
    role: str
    photo: str
    bio: str


@dataclass(frozen=True, slots=True)
class BlogPost:
    slug: str
    title: str
    category: str
    published: date
    image: str
    excerpt: str
    author: Author
    tags: tuple[str, ...]
    body_template: str = "blog/posts/demo_body.html"

    def get_absolute_url(self) -> str:
        return reverse("blog:detail", kwargs={"slug": self.slug})


_WINSTON = Author(
    name="Winston Gold",
    role="Lead Product Designer",
    photo="img/team/team-3.jpg",
    bio=(
        "Modi eum sed possimus accusantium. Quas repellat voluptatem officia numquam "
        "sint aspernatur voluptas. Esse et accusantium ut unde voluptas."
    ),
)

_JANE = Author(
    name="Jane Smith",
    role="Content Writer",
    photo="img/blog/blog-author.jpg",
    bio=(
        "Itaque quidem optio quia voluptatibus dolorem dolor. Modi eum sed possimus "
        "accusantium. Quas repellat voluptatem officia numquam sint aspernatur voluptas. "
        "Esse et accusantium ut unde voluptas."
    ),
)

_EXCERPT = (
    "Far far away, behind the word mountains, far from the countries Vokalia and "
    "Consonantia, there live the blind texts."
)

_POSTS = (
    BlogPost(
        slug="dolorum-optio-tempore-voluptas-dignissimos",
        title="Dolorum optio tempore voluptas dignissimos",
        category="Sorts",
        published=date(2022, 1, 1),
        image="img/blog/blog-1.jpg",
        excerpt=_EXCERPT,
        author=_JANE,
        tags=("Creative", "Tips", "Marketing"),
    ),
    BlogPost(
        slug="nisi-magni-odit-consequatur-autem-nulla-dolorem",
        title="Nisi magni odit consequatur autem nulla dolorem",
        category="Fashion",
        published=date(2022, 1, 1),
        image="img/blog/blog-2.jpg",
        excerpt=_EXCERPT,
        author=_WINSTON,
        tags=("Creative", "Design"),
    ),
    BlogPost(
        slug="possimus-soluta-ut-id-suscipit-soluta",
        title="Possimus soluta ut id suscipit soluta",
        category="Laws",
        published=date(2022, 7, 5),
        image="img/blog/blog-3.jpg",
        excerpt=_EXCERPT,
        author=_JANE,
        tags=("Business", "Tips"),
    ),
)

_NEWEST_FIRST = tuple(sorted(_POSTS, key=attrgetter("published"), reverse=True))
_BY_SLUG = {post.slug: post for post in _POSTS}


def all_posts() -> tuple[BlogPost, ...]:
    """Every Blog Post, newest first."""
    return _NEWEST_FIRST


def get_post(slug: str) -> BlogPost | None:
    return _BY_SLUG.get(slug)

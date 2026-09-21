"""Callers use only all_items(), get_item() and the fields, so a model can replace this module."""

from dataclasses import dataclass
from datetime import date

from django.db import models
from django.urls import reverse


class Category(models.TextChoices):
    APP = "app", "App"
    PRODUCT = "product", "Card"
    BRANDING = "branding", "Web"


@dataclass(frozen=True, slots=True)
class PortfolioItem:
    slug: str
    title: str
    summary: str
    category: Category
    image: str
    gallery: tuple[str, ...]
    client: str
    project_date: date
    project_url: str
    description_template: str = "portfolio/items/demo_description.html"

    def get_absolute_url(self) -> str:
        return reverse("portfolio:detail", kwargs={"slug": self.slug})

    # Same name Django generates for a choices field, so templates survive the move to a model.
    def get_category_display(self) -> str:
        return Category(self.category).label


_DEMO_GALLERY = (
    "img/portfolio/app-1.jpg",
    "img/portfolio/product-1.jpg",
    "img/portfolio/branding-1.jpg",
    "img/portfolio/books-1.jpg",
)


def _demo_item(slug: str, title: str, category: Category, image_number: int) -> PortfolioItem:
    return PortfolioItem(
        slug=slug,
        title=title,
        summary="Lorem ipsum, dolor sit",
        category=category,
        image=f"img/masonry-portfolio/masonry-portfolio-{image_number}.jpg",
        gallery=_DEMO_GALLERY,
        client="ASU Company",
        project_date=date(2020, 3, 1),
        project_url="https://www.example.com",
    )


_ITEMS = (
    _demo_item("app-1", "App 1", Category.APP, 1),
    _demo_item("product-1", "Product 1", Category.PRODUCT, 2),
    _demo_item("branding-1", "Branding 1", Category.BRANDING, 3),
    _demo_item("app-2", "App 2", Category.APP, 4),
    _demo_item("product-2", "Product 2", Category.PRODUCT, 5),
    _demo_item("branding-2", "Branding 2", Category.BRANDING, 6),
    _demo_item("app-3", "App 3", Category.APP, 7),
    _demo_item("product-3", "Product 3", Category.PRODUCT, 8),
    _demo_item("branding-3", "Branding 3", Category.BRANDING, 9),
)

_BY_SLUG = {item.slug: item for item in _ITEMS}


def all_items() -> tuple[PortfolioItem, ...]:
    return _ITEMS


def get_item(slug: str) -> PortfolioItem | None:
    return _BY_SLUG.get(slug)

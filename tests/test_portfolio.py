import re

from django.test import Client

ITEM_LINK = re.compile(r'href="(/portfolio/[\w-]+/)"')


def test_portfolio_lists_items_that_each_open_their_own_page(client: Client) -> None:
    item_urls = sorted(set(ITEM_LINK.findall(client.get("/portfolio/").text)))

    assert len(item_urls) == 9
    for url in item_urls:
        response = client.get(url)
        assert response.status_code == 200
        assert "Project information" in response.text


def test_portfolio_offers_a_filter_per_category(client: Client) -> None:
    response = client.get("/portfolio/")

    for value, label in [("app", "App"), ("product", "Card"), ("branding", "Web")]:
        assert f'<li data-filter=".filter-{value}">{label}</li>' in response.text
        assert f"isotope-item filter-{value}" in response.text


def test_portfolio_item_page_shows_the_item(client: Client) -> None:
    response = client.get("/portfolio/branding-2/")

    assert "<title>Branding 2 | Active</title>" in response.text
    assert "<h2>Branding 2</h2>" in response.text
    assert "<strong>Category</strong> Web" in response.text


def test_unknown_portfolio_item_is_not_found(client: Client) -> None:
    response = client.get("/portfolio/no-such-item/")

    assert response.status_code == 404
    assert "Page Not Found" in response.text

import re

import pytest
from django.test import Client

ACTIVE_NAV_LINK = re.compile(r'<a href="[^"]*" class="active">([^<]+)</a>')


@pytest.mark.parametrize(
    ("url", "title"),
    [
        ("/", "Home"),
        ("/about/", "About"),
        ("/services/", "Services"),
        ("/team/", "Team"),
        ("/portfolio/", "Portfolio"),
        ("/blog/", "Blog"),
        ("/contact/", "Contact"),
    ],
)
def test_page_renders_with_its_title_and_description(client: Client, url: str, title: str) -> None:
    response = client.get(url)

    assert response.status_code == 200
    assert f"<title>{title} | Active</title>" in response.text
    assert re.search(r'<meta name="description" content="[^"]+">', response.text)


@pytest.mark.parametrize(
    ("url", "nav_label"),
    [
        ("/", "Home"),
        ("/about/", "About"),
        ("/services/", "Services"),
        ("/portfolio/", "Portfolio"),
        ("/portfolio/app-1/", "Portfolio"),
        ("/team/", "Team"),
        ("/blog/", "Blog"),
        ("/blog/possimus-soluta-ut-id-suscipit-soluta/", "Blog"),
        ("/contact/", "Contact"),
    ],
)
def test_nav_marks_only_the_current_section_active(
    client: Client, url: str, nav_label: str
) -> None:
    response = client.get(url)

    assert ACTIVE_NAV_LINK.findall(response.text) == [nav_label]


def test_unknown_address_shows_the_styled_not_found_page(client: Client) -> None:
    response = client.get("/no-such-page/")

    assert response.status_code == 404
    assert "<title>Page Not Found | Active</title>" in response.text
    assert 'id="footer"' in response.text


@pytest.mark.urls("tests.crash_urls")
def test_server_error_shows_the_styled_error_page(client: Client) -> None:
    client.raise_request_exception = False

    response = client.get("/crash/")

    assert response.status_code == 500
    assert "<title>Server Error | Active</title>" in response.text


def test_footer_keeps_the_template_license_credit(client: Client) -> None:
    response = client.get("/")

    assert 'Designed by <a href="https://bootstrapmade.com/">BootstrapMade</a>' in response.text

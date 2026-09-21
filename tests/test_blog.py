import re

from django.test import Client

POST_LINK = re.compile(r'href="(/blog/[\w-]+/)"')


def linked_posts(html: str) -> list[str]:
    return sorted(set(POST_LINK.findall(html)))


def test_blog_lists_posts_that_each_open_their_own_page(client: Client) -> None:
    post_urls = linked_posts(client.get("/blog/").text)

    assert len(post_urls) == 3
    for url in post_urls:
        response = client.get(url)
        assert response.status_code == 200
        assert 'class="title"' in response.text


def test_blog_post_page_shows_the_post(client: Client) -> None:
    response = client.get("/blog/possimus-soluta-ut-id-suscipit-soluta/")

    assert "<title>Possimus soluta ut id suscipit soluta | Active</title>" in response.text
    assert '<h2 class="title">Possimus soluta ut id suscipit soluta</h2>' in response.text
    assert "Jul 5, 2022" in response.text


def test_blog_post_sidebar_links_to_the_other_posts(client: Client) -> None:
    current = "/blog/possimus-soluta-ut-id-suscipit-soluta/"
    response = client.get(current)

    sidebar = response.text.split('class="recent-posts-widget', 1)[1].split("</div><!--/", 1)[0]
    assert current not in sidebar
    assert len(linked_posts(sidebar)) == 2


def test_unknown_blog_post_is_not_found(client: Client) -> None:
    response = client.get("/blog/no-such-post/")

    assert response.status_code == 404
    assert "Page Not Found" in response.text


def test_blog_page_beyond_the_last_is_not_found(client: Client) -> None:
    assert client.get("/blog/?page=99").status_code == 404


def test_home_page_links_recent_posts(client: Client) -> None:
    home = client.get("/").text
    section = home.split('id="blog-posts"', 1)[1].split("</section>", 1)[0]

    assert linked_posts(section) == linked_posts(client.get("/blog/").text)


def test_footer_links_the_two_newest_posts(client: Client) -> None:
    footer = client.get("/about/").text.split('id="footer"', 1)[1]
    entries = footer.split("footer-blog-entry", 1)[1].split("</ul>", 1)[0]

    assert "/blog/possimus-soluta-ut-id-suscipit-soluta/" in entries
    assert len(linked_posts(entries)) == 2

import re
from collections import Counter

import pytest
from django.core.mail import EmailMessage
from django.test import Client

VALID_MESSAGE = {
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "subject": "Project enquiry",
    "message": "I'd like to talk about a new website.",
}


def test_valid_contact_message_is_emailed_and_confirmed(
    client: Client, mailoutbox: list[EmailMessage]
) -> None:
    response = client.post("/contact/", VALID_MESSAGE)

    assert response.status_code == 302
    assert response.url == "/contact/#contact"
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.to == ["contact@example.com"]
    assert email.reply_to == ["ada@example.com"]
    assert email.subject == "Contact Message: Project enquiry"
    assert "Ada Lovelace <ada@example.com>" in email.body
    assert VALID_MESSAGE["message"] in email.body

    confirmation = client.get(response.url)
    assert "Your message has been sent. Thank you!" in confirmation.text


def test_refreshing_after_sending_does_not_resend(
    client: Client, mailoutbox: list[EmailMessage]
) -> None:
    response = client.post("/contact/", VALID_MESSAGE, follow=True)

    client.get(response.request["PATH_INFO"])

    assert len(mailoutbox) == 1


@pytest.mark.parametrize("missing", ["name", "email", "subject", "message"])
def test_missing_field_shows_an_error_and_keeps_other_values(
    client: Client, mailoutbox: list[EmailMessage], missing: str
) -> None:
    data = {**VALID_MESSAGE, missing: ""}

    response = client.post("/contact/", data)

    assert response.status_code == 200
    assert "This field is required." in response.text
    assert "Please correct the errors above and try again." in response.text
    for field, value in data.items():
        if field != missing:
            assert value.replace("'", "&#x27;") in response.text
    assert mailoutbox == []


def test_invalid_email_shows_an_error(client: Client, mailoutbox: list[EmailMessage]) -> None:
    response = client.post("/contact/", {**VALID_MESSAGE, "email": "not-an-email"})

    assert response.status_code == 200
    assert "Enter a valid email address." in response.text
    assert mailoutbox == []


def test_multiline_subject_is_rejected(client: Client, mailoutbox: list[EmailMessage]) -> None:
    response = client.post("/contact/", {**VALID_MESSAGE, "subject": "Hi\nBcc: victim@example.com"})

    assert response.status_code == 200
    assert "The subject must be a single line." in response.text
    assert mailoutbox == []


def test_contact_form_requires_a_csrf_token(mailoutbox: list[EmailMessage]) -> None:
    response = Client(enforce_csrf_checks=True).post("/contact/", VALID_MESSAGE)

    assert response.status_code == 403
    assert mailoutbox == []


def test_newsletter_signup_returns_to_the_same_page_with_thanks(
    client: Client, mailoutbox: list[EmailMessage]
) -> None:
    response = client.post("/newsletter/", {"email": "reader@example.com", "next": "/about/"})

    assert response.status_code == 302
    assert response.url == "/about/#footer"
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Newsletter Signup"
    assert "reader@example.com" in mailoutbox[0].body

    page = client.get("/about/")
    assert page.text.count("Your subscription request has been sent. Thank you!") == 1


def test_newsletter_thanks_on_contact_page_stays_out_of_the_contact_form(
    client: Client, mailoutbox: list[EmailMessage]
) -> None:
    client.post("/newsletter/", {"email": "reader@example.com", "next": "/contact/"})

    page = client.get("/contact/")

    assert page.text.count("Your subscription request has been sent. Thank you!") == 1
    assert "Your message has been sent. Thank you!" not in page.text


def test_invalid_newsletter_email_returns_with_an_error(
    client: Client, mailoutbox: list[EmailMessage]
) -> None:
    response = client.post("/newsletter/", {"email": "nope", "next": "/team/"})

    assert response.url == "/team/#footer"
    assert "Enter a valid email address." in client.get("/team/").text
    assert mailoutbox == []


def test_newsletter_ignores_an_off_site_return_address(
    client: Client, mailoutbox: list[EmailMessage]
) -> None:
    response = client.post(
        "/newsletter/", {"email": "reader@example.com", "next": "https://evil.example/"}
    )

    assert response.url == "/#footer"


def test_newsletter_does_not_accept_get(client: Client) -> None:
    assert client.get("/newsletter/").status_code == 405


def test_every_form_field_on_the_contact_page_has_a_label(client: Client) -> None:
    html = client.get("/contact/").text

    labelled = set(re.findall(r'<label for="([^"]+)"', html))
    field_ids = re.findall(r'<(?:input|textarea)(?![^>]*type="hidden")[^>]*\bid="([^"]+)"', html)
    assert len(field_ids) == 5
    assert set(field_ids) <= labelled


def test_contact_page_element_ids_are_unique(client: Client) -> None:
    ids = Counter(re.findall(r'\bid="([^"]+)"', client.get("/contact/").text))

    assert [element_id for element_id, count in ids.items() if count > 1] == []

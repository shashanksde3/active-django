from typing import Any

from django import template
from django.template import Context

from apps.contact.forms import NewsletterForm

register = template.Library()


@register.inclusion_tag("contact/partials/newsletter_form.html", takes_context=True)
def newsletter_form(context: Context) -> dict[str, Any]:
    request = context.get("request")
    return {
        # A distinct id prefix keeps ids unique on the Contact page, which also has an email field.
        "form": NewsletterForm(auto_id="newsletter_%s"),
        "next": request.get_full_path() if request else "",
        "messages": context.get("messages", ()),
    }

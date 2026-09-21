from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import FormView

from .forms import ContactForm, NewsletterForm

CONTACT_SENT = "Your message has been sent. Thank you!"
NEWSLETTER_SENT = "Your subscription request has been sent. Thank you!"


class ContactView(FormView):
    template_name = "contact/contact.html"
    form_class = ContactForm

    def form_valid(self, form: ContactForm) -> HttpResponse:
        form.send()
        messages.success(self.request, CONTACT_SENT, extra_tags="contact")
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return f"{reverse('contact:contact')}#contact"


class NewsletterSignupView(FormView):
    form_class = NewsletterForm
    http_method_names = ["post"]

    def form_valid(self, form: NewsletterForm) -> HttpResponse:
        form.send()
        messages.success(self.request, NEWSLETTER_SENT, extra_tags="newsletter")
        return super().form_valid(form)

    def form_invalid(self, form: NewsletterForm) -> HttpResponse:
        first_error = next(iter(form.errors.values()))[0]
        messages.error(self.request, first_error, extra_tags="newsletter")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        next_url = self.request.POST.get("next", "")
        is_safe = url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        )
        return f"{next_url if is_safe else reverse('core:home')}#footer"

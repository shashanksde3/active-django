from django import forms
from django.conf import settings
from django.core.mail import EmailMessage


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Your Name"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Your Email"}),
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Subject"}),
    )
    message = forms.CharField(
        max_length=5000,
        widget=forms.Textarea(attrs={"class": "form-control", "placeholder": "Message"}),
    )

    def clean_subject(self) -> str:
        subject: str = self.cleaned_data["subject"]
        # The subject becomes an email header, where a line break is a header injection.
        if "\n" in subject or "\r" in subject:
            raise forms.ValidationError("The subject must be a single line.")
        return subject

    def send(self) -> None:
        data = self.cleaned_data
        EmailMessage(
            subject=f"Contact Message: {data['subject']}",
            body=f"From: {data['name']} <{data['email']}>\n\n{data['message']}",
            to=[settings.CONTACT_EMAIL],
            reply_to=[data["email"]],
        ).send()


class NewsletterForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter your email"}),
    )

    def send(self) -> None:
        EmailMessage(
            subject="Newsletter Signup",
            body=f"New Newsletter Signup: {self.cleaned_data['email']}",
            to=[settings.CONTACT_EMAIL],
        ).send()

"""Demo forms for testing MVPFormView."""

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Column, Fieldset, Layout, Row
from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    """Simple product form for testing MVPFormMixin."""

    class Meta:
        model = Product
        fields = ["name", "description", "price"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class ContactForm(forms.Form):
    """Simple contact form for MVPFormView testing."""

    name = forms.CharField(
        max_length=100,
        help_text="Your full name",
        widget=forms.TextInput(attrs={"placeholder": "John Doe"}),
    )
    email = forms.EmailField(
        help_text="We'll never share your email",
        widget=forms.EmailInput(attrs={"placeholder": "john@example.com"}),
    )
    subject = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Optional subject line"}),
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "Your message..."}),
        help_text="Tell us what's on your mind",
    )
    subscribe = forms.BooleanField(
        required=False,
        label="Subscribe to newsletter",
        initial=False,
    )

    def clean_message(self):
        """Validate message is at least 10 characters."""
        message = self.cleaned_data.get("message", "")
        if len(message) < 10:
            raise forms.ValidationError("Message must be at least 10 characters long.")
        return message


class LayoutDemoForm(forms.Form):
    """Groups its fields with crispy_forms Layout objects: two Fieldsets, a
    Row/Column pair inside the second, and an HTML block between them (#311).
    """

    name = forms.CharField(max_length=100, help_text="Your full name")
    email = forms.EmailField(help_text="We'll never share your email")
    address = forms.CharField(max_length=200, label="Street address")
    city = forms.CharField(max_length=100)
    postal_code = forms.CharField(max_length=20, label="Postal code")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        # form_tag=False stops {% crispy form %} adding its own <form> tag —
        # cotton/form/render.html's own comment requires this of every helper.
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset("Contact details", "name", "email"),
            HTML('<p class="text-sm opacity-70">Where should we ship your order?</p>'),
            Fieldset(
                "Shipping address",
                "address",
                Row(
                    Column("city", css_class="w-1/2"),
                    Column("postal_code", css_class="w-1/2"),
                    css_class="flex gap-4",
                ),
            ),
        )

"""Demo forms for testing MVPFormView."""

from django import forms


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

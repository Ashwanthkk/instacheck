from django import forms


class InstaForm(forms.Form):
    followers_html = forms.CharField(
        label='Followers HTML',
        widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}),
        required=True,
        help_text='Paste the HTML content from your followers file.',
    )
    following_html = forms.CharField(
        label='Following HTML',
        widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}),
        required=True,
        help_text='Paste the HTML content from your following file.',
    )

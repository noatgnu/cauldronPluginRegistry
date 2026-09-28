from django import forms


class RecipeSubmitForm(forms.Form):
    label = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'search-box'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'materialize-textarea'})
    )
    author = forms.CharField(required=False, max_length=255)
    category = forms.CharField(required=False, max_length=255)
    tags = forms.CharField(
        required=False,
        help_text='Comma-separated tags',
        widget=forms.TextInput(attrs={'placeholder': 'proteomics, differential-expression'})
    )
    data = forms.CharField(
        label='Recipe JSON',
        widget=forms.Textarea(attrs={'class': 'materialize-textarea', 'rows': 15}),
        help_text='Paste the contents of an exported recipe .json file.'
    )

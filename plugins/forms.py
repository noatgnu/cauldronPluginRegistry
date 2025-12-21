from django import forms

class PluginSubmitForm(forms.Form):
    repo_url = forms.URLField(
        label='Git Repository URL',
        max_length=200,
        widget=forms.URLInput(attrs={'class': 'search-box', 'placeholder': 'https://github.com/user/repo'})
    )

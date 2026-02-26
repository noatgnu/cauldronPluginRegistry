from django import forms
from .models import RepositorySSHKey

class PluginSubmitForm(forms.Form):
    repo_url = forms.URLField(
        label='Git Repository URL',
        max_length=200,
        widget=forms.URLInput(attrs={'class': 'search-box', 'placeholder': 'https://github.com/user/repo'})
    )

class BulkPluginSubmitForm(forms.Form):
    repo_urls = forms.CharField(
        label='Git Repository URLs',
        widget=forms.Textarea(attrs={
            'class': 'materialize-textarea',
            'placeholder': 'https://github.com/user/repo1\nhttps://github.com/user/repo2\nhttps://github.com/user/repo3'
        }),
        help_text='Enter one repository URL per line (maximum 10)'
    )

    def clean_repo_urls(self):
        data = self.cleaned_data['repo_urls']
        urls = [url.strip() for url in data.strip().split('\n') if url.strip()]

        if not urls:
            raise forms.ValidationError('Please enter at least one repository URL.')

        if len(urls) > 10:
            raise forms.ValidationError('Maximum 10 repository URLs allowed per submission.')

        for url in urls:
            if not url.startswith(('http://', 'https://', 'git@')):
                raise forms.ValidationError(f'Invalid URL format: {url}')

        return urls


class SSHKeyForm(forms.ModelForm):
    class Meta:
        model = RepositorySSHKey
        fields = ['repository_url', 'ssh_private_key', 'passphrase']
        widgets = {
            'repository_url': forms.URLInput(attrs={'class': 'validate', 'placeholder': 'git@github.com:user/repo.git'}),
            'ssh_private_key': forms.Textarea(attrs={'class': 'materialize-textarea', 'placeholder': 'Paste your SSH private key here'}),
            'passphrase': forms.PasswordInput(attrs={'class': 'validate', 'placeholder': 'Optional passphrase'})
        }
        labels = {
            'repository_url': 'Repository URL',
            'ssh_private_key': 'SSH Private Key',
            'passphrase': 'Passphrase (optional)'
        }

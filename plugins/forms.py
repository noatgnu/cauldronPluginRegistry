from django import forms
from .models import RepositorySSHKey

class PluginSubmitForm(forms.Form):
    repo_url = forms.URLField(
        label='Git Repository URL',
        max_length=200,
        widget=forms.URLInput(attrs={'class': 'search-box', 'placeholder': 'https://github.com/user/repo'})
    )

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

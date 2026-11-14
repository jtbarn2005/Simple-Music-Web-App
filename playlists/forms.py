from django import forms

from .models import Playlist


class PlaylistForm(forms.ModelForm):
    class Meta:
        model = Playlist
        fields = ['name']
        widgets = {'name': forms.TextInput(attrs={'placeholder': 'e.g. Study Mix'})}


class YouTubeLinkForm(forms.Form):
    url = forms.URLField(label='YouTube link', widget=forms.URLInput(attrs={
        'placeholder': 'Paste a YouTube video link',
    }))


class SearchForm(forms.Form):
    query = forms.CharField(label='Search YouTube', max_length=100, widget=forms.TextInput(attrs={
        'placeholder': 'Search by song, artist, or video',
        'autocomplete': 'off',
        'spellcheck': 'false',
    }))


class PlaylistChoiceForm(forms.Form):
    playlist = forms.ModelChoiceField(queryset=Playlist.objects.none(), empty_label=None)

    def __init__(self, *args, **kwargs):
        playlists = kwargs.pop('playlists', Playlist.objects.none())
        super().__init__(*args, **kwargs)
        self.fields['playlist'].queryset = playlists

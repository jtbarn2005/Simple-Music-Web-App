from django.contrib import admin

from .models import Playlist, PlaylistSong, Song


admin.site.register(Playlist)
admin.site.register(Song)
admin.site.register(PlaylistSong)

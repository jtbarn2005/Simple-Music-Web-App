from html import unescape

from django.db import migrations


def unescape_song_metadata(apps, schema_editor):
    Song = apps.get_model('playlists', 'Song')
    for song in Song.objects.all().iterator():
        updated_title = unescape(song.title)
        updated_channel = unescape(song.channel_name)
        if updated_title != song.title or updated_channel != song.channel_name:
            song.title = updated_title
            song.channel_name = updated_channel
            song.save(update_fields=['title', 'channel_name'])


class Migration(migrations.Migration):
    dependencies = [
        ('playlists', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(unescape_song_metadata, migrations.RunPython.noop),
    ]

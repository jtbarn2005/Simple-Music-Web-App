import re
import json

from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import PlaylistChoiceForm, PlaylistForm, SearchForm, YouTubeLinkForm
from .models import Playlist, PlaylistSong, Song
from .youtube import YouTubeAPIError, get_video, search_videos


YOUTUBE_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{11}$')


def extract_video_id(value):
    """Extract a video ID from common YouTube URL formats."""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtube\.com/embed/|youtube\.com/shorts/)([A-Za-z0-9_-]{11})',
        r'(?:youtu\.be/)([A-Za-z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match and YOUTUBE_ID_PATTERN.fullmatch(match.group(1)):
            return match.group(1)
    return None


def home(request):
    return render(request, 'playlists/home.html', {
        'playlists': Playlist.objects.all(),
        'playlist_form': PlaylistForm(),
    })


def search(request):
    form = SearchForm(request.GET or None)
    results = []
    api_error = None
    if form.is_valid():
        try:
            results = search_videos(form.cleaned_data['query'])
        except YouTubeAPIError as error:
            api_error = str(error)
    return render(request, 'playlists/search.html', {
        'form': form, 'results': results, 'api_error': api_error,
    })


def _save_song(video):
    song, _ = Song.objects.update_or_create(
        video_id=video['video_id'],
        defaults={key: video[key] for key in ('title', 'channel_name', 'thumbnail_url', 'source_url')},
    )
    return song


def _add_to_playlist(playlist, video):
    song = _save_song(video)
    _, created = PlaylistSong.objects.get_or_create(
        playlist=playlist, song=song,
        defaults={'position': playlist.playlist_songs.count()},
    )
    return created


def add_search_result(request):
    if request.method != 'POST':
        return redirect('playlists:search')
    video = {key: request.POST.get(key, '') for key in
             ('video_id', 'title', 'channel_name', 'thumbnail_url', 'source_url')}
    playlists = Playlist.objects.all()
    selected_id = request.POST.get('playlist_id')
    if not YOUTUBE_ID_PATTERN.fullmatch(video['video_id']):
        messages.error(request, 'That search result is invalid.')
        return redirect('playlists:search')

    try:
        video = get_video(video['video_id'])
    except YouTubeAPIError as error:
        messages.error(request, str(error))
        if selected_id:
            return redirect(f'{reverse("playlists:detail", kwargs={"playlist_id": selected_id})}?edit=1')
        return redirect('playlists:search')

    if not selected_id and playlists.count() > 1:
        return render(request, 'playlists/choose_playlist.html', {
            'video': video,
            'choice_form': PlaylistChoiceForm(playlists=playlists),
        })
    playlist = get_object_or_404(playlists, id=selected_id) if selected_id else playlists.first()
    if not playlist:
        messages.info(request, 'Create a playlist before adding a video.')
        return redirect('playlists:home')
    if _add_to_playlist(playlist, video):
        messages.success(request, f'Added “{video["title"]}” to {playlist.name}.')
    else:
        messages.warning(request, 'That video is already in this playlist.')
    return redirect(f'{reverse("playlists:detail", kwargs={"playlist_id": playlist.id})}?edit=1')


def create_playlist(request):
    if request.method != 'POST':
        return redirect('playlists:home')
    form = PlaylistForm(request.POST)
    if form.is_valid():
        playlist = form.save()
        messages.success(request, f'Created “{playlist.name}”.')
        detail_url = reverse('playlists:detail', kwargs={'playlist_id': playlist.id})
        return redirect(f'{detail_url}?edit=1')
    return render(request, 'playlists/home.html', {
        'playlists': Playlist.objects.all(),
        'playlist_form': form,
    })


def playlist_detail(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id)
    songs = playlist.playlist_songs.select_related('song')
    selected_song = songs.filter(song__video_id=request.GET.get('song')).first() if request.GET.get('song') else songs.first()
    search_form = SearchForm(request.GET or None)
    search_results = []
    search_error = None
    edit_mode = request.GET.get('edit') == '1' or 'query' in request.GET
    if search_form.is_valid():
        edit_mode = True
        try:
            search_results = search_videos(search_form.cleaned_data['query'])
        except YouTubeAPIError as error:
            search_error = str(error)
    return render(request, 'playlists/detail.html', {
        'playlist': playlist,
        'rename_form': PlaylistForm(instance=playlist),
        'link_form': YouTubeLinkForm(),
        'songs': songs,
        'selected_song': selected_song,
        'embed_origin': f'{request.scheme}://{request.get_host()}',
        'search_form': search_form,
        'search_results': search_results,
        'search_error': search_error,
        'edit_mode': edit_mode,
    })


def rename_playlist(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id)
    if request.method != 'POST':
        return redirect(f'{reverse("playlists:detail", kwargs={"playlist_id": playlist.id})}?edit=1')
    form = PlaylistForm(request.POST, instance=playlist)
    if form.is_valid():
        form.save()
        messages.success(request, 'Playlist renamed successfully.')
        return redirect(f'{reverse("playlists:detail", kwargs={"playlist_id": playlist.id})}?edit=1')
    return render(request, 'playlists/detail.html', {
        'playlist': playlist,
        'rename_form': form,
        'link_form': YouTubeLinkForm(),
        'songs': playlist.playlist_songs.select_related('song'),
        'selected_song': playlist.playlist_songs.select_related('song').first(),
        'embed_origin': f'{request.scheme}://{request.get_host()}',
        'search_form': SearchForm(),
        'search_results': [],
        'search_error': None,
        'edit_mode': True,
    })


def delete_playlist(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id)
    if request.method == 'POST':
        playlist_name = playlist.name
        playlist.delete()
        messages.success(request, f'Playlist “{playlist_name}” deleted.')
    return redirect('playlists:home')


def add_song(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id)
    if request.method != 'POST':
        return redirect('playlists:detail', playlist_id=playlist.id)
    form = YouTubeLinkForm(request.POST)
    if not form.is_valid():
        return render(request, 'playlists/detail.html', {
            'playlist': playlist,
            'rename_form': PlaylistForm(instance=playlist),
            'link_form': form,
            'songs': playlist.playlist_songs.select_related('song'),
            'selected_song': playlist.playlist_songs.select_related('song').first(),
            'embed_origin': f'{request.scheme}://{request.get_host()}',
            'search_form': SearchForm(), 'search_results': [], 'search_error': None,
            'edit_mode': True,
        })

    video_id = extract_video_id(form.cleaned_data['url'])
    if not video_id:
        form.add_error('url', 'Enter a valid YouTube video, Shorts, or youtu.be link.')
        return render(request, 'playlists/detail.html', {
            'playlist': playlist,
            'rename_form': PlaylistForm(instance=playlist),
            'link_form': form,
            'songs': playlist.playlist_songs.select_related('song'),
            'selected_song': playlist.playlist_songs.select_related('song').first(),
            'embed_origin': f'{request.scheme}://{request.get_host()}',
            'search_form': SearchForm(), 'search_results': [], 'search_error': None,
            'edit_mode': True,
        })

    try:
        video = get_video(video_id)
    except YouTubeAPIError as error:
        form.add_error('url', str(error))
        return render(request, 'playlists/detail.html', {
            'playlist': playlist,
            'rename_form': PlaylistForm(instance=playlist),
            'link_form': form,
            'songs': playlist.playlist_songs.select_related('song'),
            'selected_song': playlist.playlist_songs.select_related('song').first(),
            'embed_origin': f'{request.scheme}://{request.get_host()}',
            'search_form': SearchForm(), 'search_results': [], 'search_error': None,
            'edit_mode': True,
        })
    if not _add_to_playlist(playlist, video):
        messages.warning(request, 'That video is already in this playlist.')
    else:
        messages.success(request, 'Video added to the playlist.')
    return redirect(f'{reverse("playlists:detail", kwargs={"playlist_id": playlist.id})}?edit=1')


def remove_song(request, playlist_id, playlist_song_id):
    playlist = get_object_or_404(Playlist, id=playlist_id)
    playlist_song = get_object_or_404(PlaylistSong, id=playlist_song_id, playlist=playlist)
    playlist_song.delete()
    messages.success(request, 'Video removed from the playlist.')
    return redirect(f'{reverse("playlists:detail", kwargs={"playlist_id": playlist.id})}?edit=1')


def reorder_songs(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=405)
    try:
        song_ids = json.loads(request.body).get('song_ids', [])
        song_ids = [int(song_id) for song_id in song_ids]
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid song order.'}, status=400)

    existing_ids = set(playlist.playlist_songs.values_list('id', flat=True))
    if set(song_ids) != existing_ids or len(song_ids) != len(existing_ids):
        return JsonResponse({'error': 'The submitted queue does not match this playlist.'}, status=400)
    with transaction.atomic():
        for position, song_id in enumerate(song_ids):
            PlaylistSong.objects.filter(id=song_id, playlist=playlist).update(position=position)
    return JsonResponse({'status': 'ok'})

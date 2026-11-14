import json
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


class YouTubeAPIError(Exception):
    pass


def _get(endpoint, params):
    if not settings.YOUTUBE_API_KEY:
        raise YouTubeAPIError('The YOUTUBE_API_KEY environment variable is not configured.')
    request = Request(f'https://www.googleapis.com/youtube/v3/{endpoint}?{urlencode({**params, "key": settings.YOUTUBE_API_KEY})}')
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except (HTTPError, URLError, TimeoutError) as error:
        raise YouTubeAPIError('YouTube could not be reached right now.') from error


def _video_data(item):
    snippet = item['snippet']
    thumbnails = snippet['thumbnails']
    raw_id = item['id']
    video_id = raw_id.get('videoId') if isinstance(raw_id, dict) else raw_id
    return {
        'video_id': video_id,
        'title': unescape(snippet['title']),
        'channel_name': unescape(snippet['channelTitle']),
        'thumbnail_url': thumbnails.get('medium', thumbnails['default'])['url'],
        'source_url': f'https://www.youtube.com/watch?v={video_id}',
    }


def search_videos(query):
    data = _get('search', {'part': 'snippet', 'q': query, 'type': 'video', 'maxResults': 12,
                           'videoEmbeddable': 'true', 'videoSyndicated': 'true'})
    return [_video_data(item) for item in data.get('items', [])]


def get_video(video_id):
    data = _get('videos', {'part': 'snippet,status', 'id': video_id})
    if not data.get('items'):
        raise YouTubeAPIError('That YouTube video was not found or is unavailable.')
    item = data['items'][0]
    status = item.get('status', {})
    if status.get('privacyStatus') == 'private' or status.get('embeddable') is False:
        raise YouTubeAPIError('This video cannot be played in the embedded player and was not added.')
    return _video_data(item)

# Playlist Studio

Playlist Studio is a local Django web app for creating and managing music playlists using YouTube videos. Users can create multiple playlists, search YouTube, paste direct YouTube links, organize songs with drag-and-drop, and play videos through YouTube's embedded player.

## Instructions for Build and Use

Steps to build and/or run the software:

1. Open PowerShell in the project directory.
2. Activate the virtual environment with `.\.venv\Scripts\Activate.ps1`.
3. If needed, allow scripts for the current PowerShell session with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
4. Set the YouTube API key for the current session: `$env:YOUTUBE_API_KEY = "YOUR_API_KEY_HERE"`.
5. Start the Django development server with `python manage.py runserver`.
6. Open `http://127.0.0.1:8000/` in a web browser.

Instructions for using the software:

1. Create a playlist from the home page.
2. Open a playlist and click **Edit playlist**.
3. Search YouTube or paste a direct YouTube video link.
4. Add videos to the playlist from the search results or paste-link form.
5. Click a song to load it in the embedded YouTube player.
6. Use **Edit playlist** to reorder songs with drag-and-drop or remove songs.

## Development Environment

To recreate the development environment, you need the following software and/or libraries with the specified versions:

* Python 3.14.7
* Django 6.1.3
* SQLite, included with Python and Django
* YouTube Data API v3 and a Google Cloud API key
* A modern web browser with JavaScript enabled

## Useful Websites to Learn More

I found these websites useful in developing this software:

* [Django Documentation](https://docs.djangoproject.com/en/6.1/)
* [Django Tutorial](https://docs.djangoproject.com/en/6.1/intro/tutorial01/)
* [YouTube Data API Documentation](https://developers.google.com/youtube/data)
* [YouTube IFrame Player API](https://developers.google.com/youtube/iframe_api_reference)
* [YouTube Embedded Player Parameters](https://developers.google.com/youtube/player_parameters)

## Future Work

The following items I plan to fix, improve, and/or add to this project in the future:

* [ ] Add automated tests for playlist creation, validation, search, and reordering.
* [ ] Add import and export for local playlists.
* [ ] Improve mobile layout and accessibility.
* [ ] Add a clearer loading state for YouTube searches.

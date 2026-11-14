from django.urls import path

from . import views

app_name = 'playlists'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('search/add/', views.add_search_result, name='add_search_result'),
    path('playlists/create/', views.create_playlist, name='create_playlist'),
    path('playlists/<int:playlist_id>/', views.playlist_detail, name='detail'),
    path('playlists/<int:playlist_id>/rename/', views.rename_playlist, name='rename_playlist'),
    path('playlists/<int:playlist_id>/delete/', views.delete_playlist, name='delete_playlist'),
    path('playlists/<int:playlist_id>/add/', views.add_song, name='add_song'),
    path('playlists/<int:playlist_id>/songs/<int:playlist_song_id>/remove/', views.remove_song, name='remove_song'),
    path('playlists/<int:playlist_id>/reorder/', views.reorder_songs, name='reorder_songs'),
]

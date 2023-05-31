# %%
import math
import requests
import numpy as np
import pandas as pd
from helper import get_authorization_url, get_access_token, get_playlist_ids_from_categories, get_song_ids_from_playlists, get_spotify_songs_metadata

# %%
auth_url = get_authorization_url()
print(auth_url)

# %% 
cookie = "..."
access_token = get_access_token(cookie)
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

# %%
url = "https://api.spotify.com/v1/me/playlists"

response = requests.get(url, headers=headers)

if response.status_code == 200:
    playlists = response.json()['items']
else:
    print(f'Error: {response.status_code} - {response.json()}')

# %%
favorite_songs = []

for playlist in playlists:
    song_url = f"https://api.spotify.com/v1/playlists/{playlist['id']}/tracks"
    response = requests.get(song_url, headers=headers)

    if response.status_code == 200:
        favorite_songs.extend([song['track']['id'] for song in response.json()['items']])

batched_favorite_songs = [favorite_songs[i:i + 50] for i in range(0, len(favorite_songs), 50)]

# %%
liked_songs = pd.DataFrame()
for batch in batched_favorite_songs:
    liked_songs = get_spotify_songs_metadata(liked_songs, access_token, batch, 1, 1)

liked_songs.to_parquet('./datasets/cleaned/music-recommendation-system/liked/personal-playlists.parquet', engine='pyarrow')

# %%
genres = {
    'pop': '0JQ5DAqbMKFEC4WFtoNRpw',
    'mood': '0JQ5DAqbMKFzHmL4tf05da',
    'dance/electronic': '0JQ5DAqbMKFHOzuVTgTizF',
    'r&b': '0JQ5DAqbMKFEZPnFQSFB1T',
    'dance': '0JQ5DAqbMKFA6SOHvT3gck',
    'jazz': '0JQ5DAqbMKFAJ5xb0fwo9m',
    'classical': '0JQ5DAqbMKFPrEiAOxgac3'
}

playlist_ids = get_playlist_ids_from_categories(access_token, genres, 'TW', 5)
unheard_song_ids = get_song_ids_from_playlists(access_token, playlist_ids)

# %%
batches = math.ceil(len(unheard_song_ids) / 10)
unheard_song_ids_batches = np.array_split(unheard_song_ids, batches)

# %%
unheard_songs = pd.DataFrame()

for batch in unheard_song_ids_batches:
    unheard_songs = get_spotify_songs_metadata(unheard_songs, access_token, batch, 0, np.nan)

# %%
unheard_songs.to_parquet('./datasets/cleaned/music-recommendation-system/unheard/categories.parquet', engine='pyarrow')
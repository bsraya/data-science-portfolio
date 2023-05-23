import time
import requests
import pandas as pd
import dotenv
import urllib.parse

def get_authorization_url() -> str:
  params = {
    'client_id': dotenv.get_variable(file_path=".env.local", key="CLIENT_ID"),
    'response_type': 'code',
    'redirect_uri': 'http://localhost:3000',
    'scope': 'user-read-private user-read-email'
  }
  return f'https://accounts.spotify.com/authorize?{urllib.parse.urlencode(params)}'


def get_access_token(cookie: str) -> str:
  data = {
      'grant_type': 'authorization_code',
      'code': cookie,
      'redirect_uri': 'http://localhost:3000',
      'client_id': dotenv.get_variable(file_path=".env.local", key="CLIENT_ID"),
      'client_secret': {dotenv.get_variable(file_path=".env.local", key="CLIENT_SECRET")}
  }
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
  }
  response = requests.post('https://accounts.spotify.com/api/token', data=data, headers=headers)
  return response.json()['access_token']


def get_playlist_urls(
  access_token: str, 
  genres: list
) -> dict:
  genres_playlists = {}
  for genre in genres:
    playlist_url = f"https://api.spotify.com/v1/browse/categories/{genre}/playlists?country=NL&limit=10"

    headers = {
      'Authorization': f'Bearer {access_token}',
      'Content-Type': 'application/json'
    }
    response = requests.get(playlist_url, headers=headers)

    if response.status_code == 200:
      playlists = response.json()['playlists']['items']
      time.sleep(1)
      genres_playlists[genre] = [playlist['href'] for playlist in playlists]
    else:
      print(f'Error: {response.status_code} - {response.json()}')
      
  return genres_playlists


def get_spotify_songs_metadata(
  df: pd.DataFrame,
  access_token: str, 
  song_ids: list, 
  listen: int, 
  like: int
) -> pd.DataFrame:
  for song_id in song_ids:
    headers = {
      'Authorization': f'Bearer {access_token}',
      'Content-Type': 'application/json'
    }

    track_response = requests.get(
      f"https://api.spotify.com/v1/tracks/{song_id}",
      headers=headers
    ).json()
    
    audio_analysis_response = requests.get(
      f"https://api.spotify.com/v1/audio-features/{song_id}", 
      headers=headers
    ).json()

    time.sleep(0.1)
    row = {
      'id': track_response.get('id'),
      'title': track_response.get('name'),
      'artist(s)': ', '.join([artist['name'] for artist in track_response.get('album').get('artists')]),
      'popularity': track_response.get('popularity'),
      'danceability': audio_analysis_response.get('danceability'),
      'energy': audio_analysis_response.get('energy'),
      'key': audio_analysis_response.get('key'),
      'loudness': audio_analysis_response.get('loudness'),
      'mode': audio_analysis_response.get('mode'),
      'speechiness': audio_analysis_response.get('speechiness'),
      'acousticness': audio_analysis_response.get('acousticness'),
      'instrumentalness': audio_analysis_response.get('instrumentalness'),
      'liveness': audio_analysis_response.get('liveness'),
      'valence': audio_analysis_response.get('valence'),
      'tempo': audio_analysis_response.get('tempo'),
      'type': audio_analysis_response.get('type'),
      'id': audio_analysis_response.get('id'),
      'uri': audio_analysis_response.get('uri'),
      'track_href': audio_analysis_response.get('track_href'),
      'analysis_url': audio_analysis_response.get('analysis_url'),
      'duration_ms': audio_analysis_response.get('duration_ms'),
      'time_signature': audio_analysis_response.get('time_signature'),
      'listen': listen,
      'like': like
    }
    df = pd.concat([df, pd.DataFrame(row, index=[len(df)])])

  return df
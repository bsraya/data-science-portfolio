import os
import time
import requests
import pandas as pd
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

def get_authorization_url() -> str:
    params = {
        'client_id': os.environ['CLIENT_ID'],
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
        'client_id': os.environ['CLIENT_ID'],
        'client_secret': os.environ['CLIENT_SECRET']
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
        playlist_url = f"https://api.spotify.com/v1/browse/categories/{genre}/playlists?country=TW&limit=5"

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


def get_song_urls(access_token: str, playlists_based_on_genres: dict) -> list:
    unheard_song_ids = list()
    for key, value in playlists_based_on_genres.items():
        for url in value:
            playlist_url = f"{url}/tracks"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            response = requests.get(playlist_url, headers=headers)
            if response.status_code == 200:
                songs = response.json()['items']
                time.sleep(1)
            else:
                print(f'Error: {response.status_code} - {response.json()}')

            for song in songs:
                if song['track']['id'] not in unheard_song_ids:
                    unheard_song_ids.append(song['track']['id'])
    return unheard_song_ids


def get_spotify_songs_metadata(
    df: pd.DataFrame,
    access_token: str, 
    song_ids: list, 
    listen: int, 
    like: int
) -> pd.DataFrame:
    rows = []
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    track_responses = requests.get(
        f"https://api.spotify.com/v1/tracks?ids={'%2C'.join(song_ids)}",
        headers=headers
    ).json()
    
    time.sleep(0.5)
    
    audio_analysis_responses = requests.get(
        f"https://api.spotify.com/v1/audio-features?ids={'%2C'.join(song_ids)}",
        headers=headers
    ).json()
    
    time.sleep(0.5)

    for track_response, audio_analysis_response in zip(track_responses['tracks'], audio_analysis_responses['audio_features']):
        row = {
            'id': track_response.get('id'),
            'title': track_response.get('name'),
            'artist(s)': ', '.join([artist['name'] for artist in track_response.get('album').get('artists')]),
            'popularity': track_response.get('popularity'),
            'danceability': audio_analysis_response['danceability'],
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
        rows.append(row)

    df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    return df
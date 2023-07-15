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


def get_playlist_ids_from_categories(
    access_token: str, 
    categories: dict,
    country: str,
    no_of_playlists: int
) -> list:
    """
    Parameters:
        access_token (str): Spotify access token. (e.g. BQDZ...)
        categories (dict): A dict of categories and their IDs. (e.g. genres = { 'pop': '0JQ5DAqbMKFEC4WFtoNRpw', 'mood': '0JQ5DAqbMKFzHmL4tf05da'})
        country (str): Country code. (e.g. TW, US, ID)
        no_of_playlists (int): Number of playlists to be retrieved from each category. (e.g. 10)

    Output:
        A list of playlist URLs from one or multiple categories.
        e.g.
        genres = {
            'pop': '0JQ5...',
            ...
        }
    """

    categories_ids = dict()
    for category, category_id in categories.items():
        playlist_url = f"https://api.spotify.com/v1/browse/categories/{category_id}/playlists?country={country}&limit={no_of_playlists}"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(playlist_url, headers=headers)

        if response.status_code == 200:
            playlists = response.json()['playlists']['items']
            time.sleep(1)
            categories_ids[category] = [playlist['href'] for playlist in playlists]
        else:
            print(f'Error: {response.status_code} - {response.json()}')
        
    return categories_ids


def get_songs_from_playlists(
    access_token: str, 
    country: str,
    playlist_urls: dict
) -> list:
    """
    Parameters:
        access_token (str): Spotify access token. (e.g. BQDZ...)
        country (str): Country code. (e.g. TW, US, ID)
        playlist_urls (dict): A dict of playlist URLs from one or multiple categories. 
        (
            e.g. playlist_urls = { 
                'pop': [{playlist_url1}, {playlist_url2}, ...], 
                'mood': [{playlist_url1}, {playlist_url2}, ...], 
                ...
            }
        )
    
    Output:
        [
            {
                'genre': 'pop',
                'playlist_id': {playlist_id1}
                'song_ids': [{song_id1}, {song_id2}, ...]
            },
            
        ]
        
    """

    result = list()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    for genre, urls in playlist_urls.items():
        for url in urls:
            playlist_url = f"{url}/tracks?market={country}&fields=items%28track%28id%29%29&limit=50"
            response = requests.get(playlist_url, headers=headers)
            if response.status_code == 200:
                songs = response.json()['items']
                time.sleep(1)
            else:
                print(f'Error: {response.status_code} - {response.json()}')
            result.append({
                'genre': genre,
                'playlist_id': url.split('/')[-1],
                'song_ids': [song['track']['id'] for song in songs if song['track']['id'] is not None]
            })
    return result


def get_songs_metadata(
    df: pd.DataFrame,
    access_token: str, 
    genre: str,
    playlist_id: str,
    song_ids: list
) -> pd.DataFrame:
    rows = []
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    batches = [song_ids[i:i + 10] for i in range(0, len(song_ids), 1)]

    for batch in batches:
        track_responses = requests.get(
            f"https://api.spotify.com/v1/tracks?ids={'%2C'.join(batch)}",
            headers=headers
        ).json()
        time.sleep(0.1)
        
        audio_analysis_responses = requests.get(
            f"https://api.spotify.com/v1/audio-features?ids={'%2C'.join(batch)}",
            headers=headers
        ).json()
        time.sleep(0.1)

        for track_response, audio_analysis_response in zip(track_responses['tracks'], audio_analysis_responses['audio_features']):
            if audio_analysis_response is None:
                continue

            row = {
                'id': track_response.get('id'),
                'title': track_response.get('name'),
                'playlist_id': playlist_id,
                'category': genre,
                'artist(s)': ', '.join([artist['name'] for artist in track_response.get('album').get('artists')]),
                'popularity': track_response.get('popularity', 0),
                'danceability': audio_analysis_response.get('danceability', 0),
                'energy': audio_analysis_response.get('energy', 0),
                'key': audio_analysis_response.get('key', 0),
                'loudness': audio_analysis_response.get('loudness', 0),
                'mode': audio_analysis_response.get('mode', 0),
                'speechiness': audio_analysis_response.get('speechiness', 0),
                'acousticness': audio_analysis_response.get('acousticness', 0),
                'instrumentalness': audio_analysis_response.get('instrumentalness', 0),
                'liveness': audio_analysis_response.get('liveness', 0),
                'valence': audio_analysis_response.get('valence', 0),
                'tempo': audio_analysis_response.get('tempo', 0),
                'type': audio_analysis_response.get('type'),
                'uri': audio_analysis_response.get('uri'),
                'track_href': audio_analysis_response.get('track_href'),
                'analysis_url': audio_analysis_response.get('analysis_url'),
                'duration_ms': audio_analysis_response.get('duration_ms', 0),
                'time_signature': audio_analysis_response.get('time_signature', 0),
                'listen': 0
            }
            rows.append(row)

    df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    return df
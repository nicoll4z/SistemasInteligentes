import os
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from functools import wraps
import random
import pandas as pd
import sklearn
from sklearn.metrics import pairwise
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import time


app = Flask(__name__)
app.secret_key = os.urandom(64)
app.config["SESSION_COOKIE_NAME"] = "spotify-auth-session"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True


client_id = "ae3bf4d7490d479a96bd35bc0574811b"
client_secret = "d3ab51b275a644558e71e2ff1aa4dbda"
redirect_uri = "http://localhost:5000/callback"
scope = "user-library-read playlist-read-private user-top-read user-read-private playlist-modify-public"

auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, 
                            scope=scope, cache_path=".spotifycache", show_dialog=True)

sp = Spotify(auth_manager=auth_manager)
user_id = sp.me()['id']
guardaId = ''
guarda_ids = ''

def getPlaylistId(sp,user_id):
    global guardaId 
    if guardaId == '':
        playlist = sp.user_playlist_create(user_id, 'Spotify Recommender', public=True, description='Playlist criada utilizando um sistema inteligente') 
        guardaId = playlist['id']
        return (guardaId)
    else:
        return (guardaId)

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route('/login')
def login():
    auth_url = auth_manager.get_authorize_url()
    return render_template("login.html", auth_url=auth_url)


@app.route('/callback')
def callback():
    if request.args.get("code"):
        token_info = auth_manager.get_access_token(request.args.get("code"), check_cache=False)
        session["spotify_token"] = token_info["access_token"]
        session["spotify_token_expiry"] = token_info["expires_in"] + time.time()
        session["spotify_refresh_token"] = token_info["refresh_token"]

        return redirect('/')
    
    flash("Error when logging in")
    return redirect('/login')


@app.route('/log_out')
def log_out():
    session.clear()
    return redirect('/login')



def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        
        if "spotify_token" not in session:
            return redirect('/login')
        
        token_expiry = session.get('spotify_token_expiry')
        if token_expiry != None and token_expiry < time.time():
            refresh_token = session.get('spotify_refresh_token')
            new_token_info = auth_manager.refresh_access_token(refresh_token)
            session['spotify_token'] = new_token_info['access_token']
            session['spotify_token_expiry'] = new_token_info['expires_in'] + time.time()
        
        return f(*args, **kwargs)
    return decorated


@app.route('/user_informations')
@requires_auth
def user_informations():
    sp = Spotify(auth_manager=auth_manager)

    username = sp.me()['display_name']
    user_picture = sp.me()['images'][0]['url']

    return jsonify(username=username, user_picture=user_picture)


@app.route('/')
@requires_auth
def index():
    return render_template("index.html")


def get_top_tracks_by_country(limit=50):
    global sp
    country_name = sp.me()['country']

    search_query = f"Top 50 - {country_name}"
    results = sp.search(q=search_query, type="playlist", limit=1)
    
    if results['playlists']['items']:
        playlist_id = results['playlists']['items'][0]['id']
        tracks = sp.playlist_tracks(playlist_id, limit=limit)
        return [track["track"]["id"] for track in tracks["items"] if track["track"]["id"]]
    else:
        print(f"Playlist 'Top 50 - {country_name}' não encontrada.")
        return []

def get_top_tracks_global(limit=100):
    global sp
    playlist_id = '5dnSFdz51E2Qouk7iFnwbl'
    tracks = sp.playlist_tracks(playlist_id, limit=limit)
    return [track["track"]["id"] for track in tracks["items"] if track["track"]["id"]]
 

def get_top_tracks_eua(limit=100):
    global sp
    playlist_id = '37i9dQZEVXbLRQDuF5jeBp'
    tracks = sp.playlist_tracks(playlist_id, limit=limit)
    return [track["track"]["id"] for track in tracks["items"] if track["track"]["id"]]

def get_top_tracks_br(limit=100):
    global sp
    playlist_id = '1bvMJOjRUUNNVXCoR1Oi6v'
    tracks = sp.playlist_tracks(playlist_id, limit=limit)
    return [track["track"]["id"] for track in tracks["items"] if track["track"]["id"]]
  

def get_recommend_spotify():
    global sp
    global user_id

    favorite_artists = sp.current_user_top_artists(limit=5)['items']
    artists_id = [artist['id'] for artist in favorite_artists]
  
    recommended_tracks = sp.recommendations(seed_artists=artists_id, limit=100)['tracks']
    tracks_id = [track['id'] for track in recommended_tracks]
    
    return tracks_id

def data_frame_features(escolha):
    country_tracks = get_top_tracks_by_country()
    global_tracks = get_top_tracks_global()
    tracks_recommended = get_recommend_spotify()
    top_tracks = get_top_tracks_user()
    eua_tracks = get_top_tracks_eua()
    br_tracks = get_top_tracks_br()
    
    audio_features = sp.audio_features(country_tracks)
    audio_features2 = sp.audio_features(tracks_recommended)
    audio_features3 = sp.audio_features(global_tracks)
    audio_features4 = sp.audio_features(top_tracks)
    audio_features5 = sp.audio_features(eua_tracks)
    audio_features6 = sp.audio_features(br_tracks)
    
    
    
    track_data = [
    {
        'id': features['id'],
        'bpm': features['tempo'],
        'energia': features['energy'],
        'valence': features['valence'],
        'danceabilidade': features['danceability']
    }
    for features in audio_features + audio_features2 + audio_features3 + audio_features5 + audio_features6 if features
    ]
    
    top_tracks_data = [
    {
        'id': features['id'],
        'bpm': features['tempo'],
        'energia': features['energy'],
        'valence': features['valence'],
        'danceabilidade': features['danceability']
    }
    for features in audio_features4 if features
    ]
    
    df_tracks = pd.DataFrame(track_data)
    df_top_tracks = pd.DataFrame(top_tracks_data)
    
    if escolha == 1:
        return df_tracks
    elif escolha == 2:
        return df_top_tracks
    
          

def get_top_tracks_user(limit=50):
    global sp
    top_tracks = sp.current_user_top_tracks(limit=limit)
    track_ids = [track['id'] for track in top_tracks['items']]
    return track_ids

    
def get_recomendation():
    scaler = StandardScaler()
    aux = 1
    df_tracks = data_frame_features(aux)
    aux = 2
    df_tracks_train = data_frame_features(aux)
    global guarda_ids

    
    df_tracks[['energia', 'valence', 'bpm', 'danceabilidade']] = scaler.fit_transform(df_tracks[['energia', 'valence', 'bpm', 'danceabilidade']])
    features = ['bpm', 'energia', 'valence', 'danceabilidade']
    
    # Matriz de similaridade
    similarity_matrix = cosine_similarity(df_tracks_train[features], df_tracks[features])  
    
    # Para armazenar os IDs das 50 músicas mais similares
    top_similar_ids = []

    # Para cada música do conjunto de treino, encontre os IDs das 2 músicas mais similares
    for i in range(similarity_matrix.shape[0]):  # iterar sobre cada música no conjunto de treino
        similar_indices = similarity_matrix[i].argsort()[2:-1]  # Pega os 2 mais similares (excluindo a própria música)
        similar_ids = df_tracks.iloc[similar_indices]['id'].tolist()  # Obtém os IDs
        for similar_id in similar_ids:
            if similar_id not in guarda_ids:
                top_similar_ids.append(similar_id)  # Adiciona à lista

    
    # Remova duplicatas e limite a 50 IDs se necessário
    top_similar_ids = list(set(top_similar_ids))[:51]
    guarda_ids = top_similar_ids
     

    return top_similar_ids
    
@app.route('/songs')
@requires_auth
def songs_recommendation():
    global sp
    global user_id

    playlist_id = getPlaylistId(sp, user_id)
 
    tracks_id = get_recomendation()

    if isinstance(tracks_id, list) and all(isinstance(i, list) for i in tracks_id):
        tracks_id = [item for sublist in tracks_id for item in sublist]
        
    sp.playlist_add_items(playlist_id, tracks_id)

    return render_template('songs.html', playlist_id=playlist_id)

@app.route('/get_new_playlist')
def get_new_playlist():
    global sp 
    global user_id 
    global tracks_id

    playlist_id = getPlaylistId(sp, user_id)
    playlist_tracks = sp.playlist_tracks(playlist_id)
    track_uris = [item['track']['uri'] for item in playlist_tracks['items']]
    
    sp.playlist_remove_all_occurrences_of_items(playlist_id, track_uris)
    
    tracks_id = get_recomendation()

    if isinstance(tracks_id, list) and all(isinstance(i, list) for i in tracks_id):
        tracks_id = [item for sublist in tracks_id for item in sublist]


    sp.playlist_add_items(playlist_id, tracks_id)

    return jsonify(playlist_id=playlist_id)


if __name__ == "__main__":
    app.run(port=5000, debug=False)
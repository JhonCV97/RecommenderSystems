import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Autenticación en la API de Spotify
client_id = "8e8ee105093a4ef8b4c147293e9ff90d"
client_secret = "1e583ff02a9249a8bd1253a636fee613"
redirect_uri = "http://localhost:8888/callback"

song_name_input = input("Ingrese el nombre de la cancion: ")
artist_name_input = input("Ingrese el nombre del artista: ")

# Flujo de autorización OAuth
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="user-read-playback-state,user-library-read"
    )
)

song_name = song_name_input
artist_name = artist_name_input

query = f'{song_name} artist:{artist_name}'
result = sp.search(q=query, type='track', limit=1)

if not result['tracks']['items']:
    print('No se encontro la cancion')
else:
    track_id = result['tracks']['items'][0]['id']
    recommendations = sp.recommendations(seed_tracks=[track_id], limit=10)

    total = 0
    tracks = []
    for item in recommendations['tracks']:
        tracks_album = sp.album_tracks(item['album']['id'])
        for track in tracks_album['items']:
            tracks.append(track['id'])

    # Eliminar duplicados
    tracks = list(set(tracks))
    print(f'Total de canciones evaluadas {len(tracks)}')
    print('Cargando...')
    # Obtener metadatos de las canciones de las playlists
    track_features = []
    for track_id in tracks:
        features = sp.audio_features(track_id)[0]  # Agregar [0] para obtener el diccionario de características
        features['id'] = track_id  # Agregar el ID de la canción al diccionario de características
        track_features.append(features)

    # Crear un DataFrame con los metadatos de las canciones
    df_tracks = pd.DataFrame(track_features)

    # Seleccionar una canción de referencia
    reference_track_id = track_id
    # Agregar [0] para obtener el diccionario de características
    reference_track_features = sp.audio_features(reference_track_id)[0]

    # Calcular la distancia entre la canción de referencia y cada canción del historial de reproducción
    distances = []
    for index, track_features in df_tracks.iterrows():
        feature_values = track_features.drop(
            labels=['id', 'type', 'uri', 'track_href', 'analysis_url', 'time_signature'])
        ref_feature_values = pd.Series(reference_track_features).drop(
            labels=['id', 'type', 'uri', 'track_href', 'analysis_url', 'time_signature'])
        distance = np.linalg.norm(feature_values - ref_feature_values)
        distances.append(distance)

    # Ordenar las canciones por distancia (menor distancia primero)
    df_tracks['distance'] = distances
    df_tracks = df_tracks.sort_values(by=['distance'], ascending=True)

    # Obtener recomendaciones
    recommended_track_ids = df_tracks['id'].head(10).tolist()

    # Obtener metadatos de las canciones recomendadas
    recommended_tracks = []
    for track_id in recommended_track_ids:
        track = sp.track(track_id)
        recommended_tracks.append(track)

    # Imprimir las canciones recomendadas
    print("Canciones recomendadas:")
    print(" ")
    for track in recommended_tracks:
        print(track['name'] + " by " + track['artists'][0]['name'])

    # Crear gráficos
    # Distribución de distancias
    plt.figure(figsize=(10, 6))
    plt.hist(df_tracks['distance'], bins=30, edgecolor='k', alpha=0.7)
    plt.title('Distribución de Distancias entre canciones evaluadas y la Canción de Referencia')
    plt.xlabel('Distancia')
    plt.ylabel('Frecuencia')
    plt.show()

    # Comparación de características
    features_to_compare = ['danceability', 'energy', 'valence', 'tempo']
    reference_values = [reference_track_features[feature] for feature in features_to_compare]
    recommended_values = df_tracks[features_to_compare].head(10).mean().values

    x = np.arange(len(features_to_compare))  # El número de características
    width = 0.35  # El ancho de las barras

    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width / 2, reference_values, width, label='Canción de Referencia')
    rects2 = ax.bar(x + width / 2, recommended_values, width, label='Canciones Recomendadas')

    # Añadir etiquetas, título y leyenda
    ax.set_ylabel('Valor')
    ax.set_title('Comparación de Características entre la Canción de Referencia y las Canciones Recomendadas')
    ax.set_xticks(x)
    ax.set_xticklabels(features_to_compare)
    ax.legend()

    fig.tight_layout()
    plt.show()
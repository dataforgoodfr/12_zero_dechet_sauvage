import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import plotly.express as px
import folium
from streamlit_folium import folium_static
from folium import IFrame
import warnings

warnings.filterwarnings('ignore')

# chemin d'accès des fichiers de données
DATA_PATH = 'https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visualisation/data/data_zds_enriched.csv'
CORRECTION = 'https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/1-exploration-des-donn%C3%A9es/Exploration_visualisation/data/releves_corrects_surf_lineaire.xlsx'
DATA_SPOT = 'https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/1-exploration-des-donn%C3%A9es/Exploration_visualisation/data/export_structures_29022024.xlsx'

# fichier geojson pour localisation folium
FRANCE_DPTS = "departements-version-simplifiee.geojson"
FRANCE_REGIONS = "regions-avec-outre-mer.geojson"

# importation des données
data = pd.read_csv(DATA_PATH)
correction = pd.read_excel('releves_corrects_surf_lineaire.xlsx')
correction = correction.rename(columns={'DEF_\nSURFACE': 'DEF_SURFACE'})
spot = pd.read_excel('export_spots_02042024.xlsx')

# fusion et correction
data_corect = pd.merge(data, correction, on='ID_RELEVE', how='left')
data = data_corect[data_corect['DEF_SURFACE'] == 'OUI']

# Calcul de la densité
data['DENSITE'] = data['VOLUME_TOTAL']/data['SURFACE']
data = data[data['DENSITE'] < 20] # suppression d'une ligne avec une valeur de densité aberrante

data['DENSITE'] = data['DENSITE'].round(4)
data['SURFACE_ROND'] = data['SURFACE'].round(2)

couleur =  {
            'Littoral (terrestre)': 'lightblue',
            'Mer - Océan': 'darkblue',
            'Cours d\'eau': 'cyan',
            'Zone naturelle ou rurale (hors littoral et montagne)': 'green',
            'Zone urbaine': 'orange',
            'Lagune et étang côtier': 'red',
            'Multi-lieux': 'pink',
            'Montagne': 'grey',
            'Présent au sol (abandonné)': 'black'}

def couleur_milieu(type):
    return couleur.get(type, 'white')

# Configuration de la page
st.set_page_config(
    layout="wide", page_title="Dashboard Zéro Déchet Sauvage : onglet Hotspots"
)

# Session state
session_state = st.session_state

# Récupérer les filtres géographiques s'ils ont été fixés
filtre_niveau = st.session_state.get("niveau_admin", "")
filtre_collectivite = st.session_state.get("collectivite", "")

# Titre de l'onglet
st.markdown("""# 🔥 Hotspots : **Quelles sont les zones les plus impactées ?**""")
st.markdown("---")

# Create side-by-side containers for indicators
indicator_col1, indicator_col2, indicator_col3 = st.columns(3)
with indicator_col1:
    st.info(f'Densité Moyenne : {data['DENSITE'].mean().round(4)}')
with indicator_col2:
    st.warning(f'Volume Moyen : {data['VOLUME_TOTAL'].mean().round(4)}')
with indicator_col3:
    st.error(f'Surface Moyenne : {data['SURFACE'].mean().round(4)}')

st.markdown("---")

left_column, right_column = st.columns([2, 1])

with left_column:

    st.markdown("### Carte des Hotspots")
    gdf = gpd.read_file(FRANCE_REGIONS)

    m = folium.Map(location=[data['LIEU_COORD_GPS_Y'].mean(), data['LIEU_COORD_GPS_X'].mean()])

    for index, row in data.iterrows():

        popup_html = f"""
        <div style="width: 300px; height: 130px;">
            <h3>Densité: {row['DENSITE']} L/m²</h3>
            <h4>Volume total : {row['VOLUME_TOTAL']} litres</h4>
            <h4>Surface total : {row['SURFACE_ROND']} m²</h4>
            <h4>Type de milieu : {row['TYPE_MILIEU']}</h4>
        </div>
        """
        lgd_txt = '<span style="color: {col};">{txt}</span>'
        color = couleur_milieu(row['TYPE_MILIEU'])
        folium.CircleMarker(
            fg = folium.FeatureGroup(name= lgd_txt.format( txt= ['TYPE_MILIEU'], col= color)),
            location=[row['LIEU_COORD_GPS_Y'], row['LIEU_COORD_GPS_X']],
            radius=np.log(row['DENSITE'] + 1)*15,  
            popup=folium.Popup(popup_html, max_width=300),
            color=color,
            fill=True,
            
        ).add_to(m)

    folium_static(m)


with right_column:

    st.markdown("### Tableau des Densités")
    table_milieu = data.groupby('TYPE_MILIEU')['DENSITE'].mean().reset_index().sort_values(by='DENSITE', ascending=False)
    table_milieu['DENSITE'] = table_milieu['DENSITE'].round(4)

    st.dataframe(table_milieu,
                column_order=("TYPE_MILIEU", "DENSITE"),
                hide_index=True,
                width=None,
                column_config={
                    "TYPE_MILIEU": st.column_config.TextColumn(
                        "Milieu",
                    ),
                    "DENSITE": st.column_config.NumberColumn(
                        "Densité (L/m²)",
                        format="%f",
                        min_value=0,
                        max_value=max(table_milieu['DENSITE']),
                    )}
                )

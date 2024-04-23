import streamlit as st

# import altair as alt # Unused for now
import pandas as pd
import numpy as np
import geopandas as gpd

# import duckdb # Unused for now

# import for choropleth map
import requests
import plotly.express as px

# import for line chart
import plotly.graph_objects as go

# To show folium maps on streamlit
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static, st_folium


###################################
# Parameters for the hotspots tab #
###################################

# This dict map the name of the "niveaux admin" as define in the home tab and the
# column name in the data_zds df. The "niveaux_admin" selection is store in the session state.
NIVEAUX_ADMIN_DICT = {
    "Région": "REGION",
    "Département": "DEP_CODE_NOM",
    "EPCI": "LIBEPCI",
    "Commune": "COMMUNE_CODE_NOM",
}

# The name of the "niveau_admin" fetch from the session state
NIVEAU_ADMIN = st.session_state["niveau_admin"]

# The name of the "niveau_admin" column in the data_zds df
NIVEAU_ADMIN_COL = NIVEAUX_ADMIN_DICT[NIVEAU_ADMIN]

# The value selected for the "niveau_admin" column fetch from the session state
NIVEAU_ADMIN_SELECTION = st.session_state["collectivite"]

# Data path for the df_nb_dechets
NB_DECHETS_PATH = (
    "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
    "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
    "sation/data/data_releve_nb_dechet.csv"
)

# Data path for the data_zds path
DATA_ZDS_PATH = (
    "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
    "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
    "sation/data/data_zds_enriched.csv"
)

# Data path for the France regions geojson
REGION_GEOJSON_PATH = (
    "https://raw.githubusercontent.com/dataforgoodfr/"
    "12_zero_dechet_sauvage/1-exploration-des-donn%C3%A9es/"
    "Exploration_visualisation/data/regions-avec-outre-mer.geojson"
)

# Data path for Correction
CORRECTION = (
    "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/"
    "1-exploration-des-donn%C3%A9es/Exploration_visualisation/data/"
    "releves_corrects_surf_lineaire.xlsx"
)

# Data path for Data Spot
DATA_SPOT = (
    "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/"
    "raw/1-exploration-des-donn%C3%A9es/Exploration_visualisation"
    "/data/export_structures_29022024.xlsx"
)

# Params for the adopted spots map filters
ADOPTED_SPOTS_FILTERS_PARAMS = [
     {
        "filter_col": "REGION",
        "filter_message": "Sélectionnez une région (par défaut votre région) :",
    },
    {"filter_col": "TYPE_MILIEU", "filter_message": "Sélectionnez un milieu :"},
    {"filter_col": "ANNEE", "filter_message": "Sélectionnez une année :"},
]

# Params for the density graph filters
DENSITY_FILTERS_PARAMS = [
    {"filter_col": "TYPE_MILIEU", "filter_message": "Sélectionnez un milieu :"},
    {"filter_col": "TYPE_LIEU2", "filter_message": "Sélectionnez un lieu :"}
]


#########################
# 0/ Page configuration #
#########################

# Session state
session_state = st.session_state

# Récupérer les filtres géographiques s'ils ont été fixés
filtre_niveau = st.session_state.get("niveau_admin", "")
filtre_collectivite = st.session_state.get("collectivite", "")

# Set the streamlit page config
st.set_page_config(
    page_title="Hotspots", layout="wide", initial_sidebar_state="expanded"
)

# Execute code page if the authentication was complete
if st.session_state["authentication_status"]:
    # Check if the filtre for "niveau administratif" and for the "collectivité" were selected in the home tab
    if filtre_niveau == "" and filtre_collectivite == "":
        st.write("Aucune sélection de territoire n'a été effectuée")

    else:
        st.write(f"Votre territoire : {filtre_niveau} {filtre_collectivite}")

    # Call the dataframes data_zds and nb_dechets filtered from the session state
    if ("df_other_filtre" not in st.session_state) or (
        "df_nb_dechets_filtre" not in st.session_state
    ):
        st.write(
            """
                ### :warning: Merci de sélectionner une collectivité\
                dans l'onglet Home pour afficher les données. :warning:
                """
        )
        st.stop()
    else:
        data_zds = st.session_state["df_other_filtre"].copy()
        df_nb_dechet = st.session_state["df_nb_dechets_filtre"].copy()


###########################################################################
# 0 bis/ Fonctions utilitaires : peuvent être utilisées par tout le monde #
###########################################################################


def construct_query_string(bound_word=" and ", **params) -> str:
    """Construct a query string in the right format for the pandas 'query'
    function. The different params are bounded together in the query string with the
    bound word given by default. If one of the params is 'None', it is not
    included in the final query string."""

    # Instanciate query string
    query_string = ""

    # Iterate over the params to construct the query string
    for param_key, param in params.items():
        # Construct the param sub string if the param is not 'None'
        if param:

            # Check if the parameter value is of type int
            if isinstance(param, int):
                # If it's an integer, use integer comparison
                query_sub_string = f"{param_key} == {param}"

            # Check if the parameter value is a list.
            elif isinstance(param, list):
                # Handle list of values for multiselect queries.
                param_values = ", ".join(
                    [f'"{value}"' for value in param]
                )  # Prepare string of values enclosed in quotes.
                query_sub_string = (
                    f"{param_key} in [{param_values}]"  # Use 'in' operator for lists.
                )

            else:
                # Create a query sub-string for other data types
                query_sub_string = f'{param_key} == "{param}"'

            # Add to the query string
            query_string += f"{query_sub_string}{bound_word}"

    # Strip any remaining " and " at the end of the query string
    return query_string.strip(bound_word)


def scalable_filters_single_select(
    data_zds: pd.DataFrame,
    filters_params=ADOPTED_SPOTS_FILTERS_PARAMS,
    base_key="default_key",
) -> dict:
    """Create streamlit select box filters as specified by the filters_params list.
    Create the filter dict used to filter the hotspots maps accordingly."""

    # Instanciate the empty filter dict
    filter_dict = dict()

    # Create as many columns as the lenght of the filters_params list
    columns = st.columns(len(filters_params))

    # Iterate over filters_params
    for i, filter_params in enumerate(filters_params):
        # Set the filter column and the filter message
        column, message = filter_params["filter_col"], filter_params["filter_message"]

        # Sort the unique values of the column in ascending order
        sorted_values = sorted(data_zds[column].unique(), reverse=True)

        # Create unique values and sort them in descending order
        unique_key = f"{base_key}_{column}_{i}"

        # Create the Streamlit select box with sorted values and a unique key
        s = columns[i].selectbox(message, sorted_values, key=unique_key)

        # Show the select box on screen
        columns[i].write(s)

        # Fill the filter dict
        filter_dict[column] = s

    return filter_dict


def scalable_filters_multi_select(
    data_zds: pd.DataFrame,
    filters_params=DENSITY_FILTERS_PARAMS,
    base_key="default_key",
) -> dict:
    """Create streamlit select box filters as specified by the filters_params list.
    Create the filter dict used to filter the hotspots maps accordingly."""

    # Instanciate the empty filter dict
    filter_dict = dict()

    # Create as many columns as the lenght of the filters_params list
    columns = st.columns(len(filters_params))

    # Iterate over filters_params
    for i, filter_params in enumerate(filters_params):
        # Set the filter column and the filter message
        column, message = filter_params["filter_col"], filter_params["filter_message"]

        # Get unique values, convert to string and sort them
        sorted_values = sorted(
            data_zds[column].dropna().astype(str).unique(), reverse=True
        )

        # Generate a unique key for each multiselect widget
        unique_key = f"{base_key}_{column}_{i}"

        # Create the Streamlit multiselect with sorted values and a unique key
        selected_values = columns[i].multiselect(
            message,
            sorted_values,
            default=sorted_values[0] if sorted_values else [],
            key=unique_key,
        )

        # Fill the filter dict with the selected values
        filter_dict[column] = selected_values

    return filter_dict


def construct_admin_lvl_boundaries(
    admin_lvl: str, single_filter_dict: dict, admin_lvl_geojson_path_dict: dict
) -> any:
    """"""

    # Unpack the admin level geojson path
    admin_lvl_geojson_path = admin_lvl_geojson_path_dict[f"{admin_lvl}"]

    # Unpack the region name
    admin_lvl_name = single_filter_dict[f"{admin_lvl}"]

    # Load France regions from a GeoJSON file
    admin_lvl_shapes = gpd.read_file(admin_lvl_geojson_path)

    # Filter the region geodataframe for the specified region
    selected_admin_lvl = admin_lvl_shapes[
        admin_lvl_shapes["nom"].str.lower() == admin_lvl_name.lower()
    ]
    if selected_admin_lvl.empty:
        raise KeyError(f"Administrative level '{admin_lvl_name}' not found.")

    return selected_admin_lvl


##################
# 1/ Import data #
##################

# Load all regions from the GeoJSON file
regions = gpd.read_file(REGION_GEOJSON_PATH)

# nb dechets : Unused for now
# df_nb_dechets = pd.read_csv(NB_DECHETS_PATH)

# data_zds : main source of data for the hotspots tab
# /!\ Already loaded from the streamlit session state defined in the home tab
# data_zds = pd.read_csv(DATA_ZDS_PATH)

# spot:
# spot = pd.read_excel(DATA_SPOT)

# correction : corrected data for density map
correction = pd.read_excel(CORRECTION)

# Fusion and correction
data_correct = pd.merge(data_zds, correction, on="ID_RELEVE", how="left")
data_correct = data_correct[data_correct["SURFACE_OK"] == "OUI"]
data_zds = data_correct[data_correct["VOLUME_TOTAL"] > 0]

##################
# 2/ Hotspot tab #
##################

# Tab title
st.markdown("""# 🔥 Hotspots : **Quelles sont les zones les plus impactées ?**""")


########################################################
# 2.1/ Carte densité de déchets sur les zones étudiées #
########################################################

def calculate_and_display_metrics(data, indicator_col1, indicator_col2, indicator_col3):
    # Calculate density
    data['DENSITE'] = data['VOLUME_TOTAL'] / data['SURFACE']
    data = data[data['DENSITE'] < 20]  # Remove rows with anomalously high density values



    # Display metrics in specified UI containers
    cell1 = indicator_col1.container(border=True)
    cell1.metric("Densité Moyenne :", f"{data['DENSITE'].mean().round(4)} L/m²")

    cell2 = indicator_col2.container(border=True)
    cell2.metric("Volume Moyen :", f"{data['VOLUME_TOTAL'].mean().round(2)} Litres")

    cell3 =  indicator_col3.container(border=True)
    cell3.metric("Surface Moyenne :", f"{data['SURFACE'].mean().round(2):,} m²")

    return data

# Define the colors representing les différents 'Lieux' et 'Milieux'
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

# Function to retrieve the color associated with a given environment type
def couleur_milieu(type):
    return couleur.get(type, 'white') # Returns 'white' if the type is not found

# Function to plot a density map
def plot_density_map(
    data_zds: pd.DataFrame,
    region_geojson_path: str,
) -> folium.Map:

    # Read geographic data from a GeoJSON file
    gdf = gpd.read_file(region_geojson_path)

    # Calculate density
    data_zds['DENSITE'] = data_zds['VOLUME_TOTAL']/data_zds['SURFACE']
    data_zds = data_zds[data_zds['DENSITE'] < 20] # Remove rows with anomalously high density values

    # Round density values for display
    data_zds['DENSITE'] = data_zds['DENSITE'].round(4)
     # Round surface values for display
    data_zds['SURFACE_ROND'] = data_zds['SURFACE'].round(2)

    # Initialize a map centered at the mean coordinates of locations
    m = folium.Map(location=[data_zds['LIEU_COORD_GPS_Y'].mean(), data_zds['LIEU_COORD_GPS_X'].mean()])

    # Loop over each row in the DataFrame to place markers
    for index, row in data_zds.iterrows():
        popup_html = f"""
        <div style="width: 300px; height: 170px;">
            <h4>Densité: {row['DENSITE']} L/m²</h4>
            <h4>Volume total : {row['VOLUME_TOTAL']} litres</h4>
            <h4>Surface total : {row['SURFACE_ROND']} m²</h4>
            <h4>Type de milieu : {row['TYPE_MILIEU']}</h4>
            <h4>Type de lieu : {row['TYPE_LIEU']}</h4>
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

# Function for 'milieu' density table

def density_table(data_zds: pd.DataFrame):

    # Calculate density
    data_zds['DENSITE'] = data_zds['VOLUME_TOTAL'] / data_zds['SURFACE']
    # Remove rows with anomalously high density values
    data_zds = data_zds[data_zds['DENSITE'] < 20]

    # Group by 'TYPE_MILIEU', calculate mean density, sort, and round the density
    table_milieu = (
        data_zds.groupby('TYPE_MILIEU')['DENSITE']
        .mean()
        .reset_index()
        .sort_values(by='DENSITE', ascending=False)
    )
    table_milieu['DENSITE'] = table_milieu['DENSITE'].round(4)

    st.dataframe(table_milieu,
                column_order=("TYPE_MILIEU", "DENSITE"),
                hide_index=True,
                width=800,
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


################################
# 2.1/ Carte des spots adoptés #
################################

# Create the map of the adopted spots
def plot_adopted_waste_spots(
    data_zds: pd.DataFrame,
    single_filter_dict: dict,
    region_geojson_path: str,
) -> folium.Map:
    """Show a folium innteractive map of adopted spots within a selected region,
    filtered by environments of deposit.
    Arguments:
    - data_zds: The waste dataframe
    - filter_dict: dictionary mapping the name of the column in the waste df and the value you want to filter by
    """

    # 1/ Create the waste geodataframe #
    # Create a GeoDataFrame for waste points
    gdf = gpd.GeoDataFrame(
        data_zds,
        geometry=gpd.points_from_xy(
            data_zds["LIEU_COORD_GPS_X"], data_zds["LIEU_COORD_GPS_Y"]
        ),
        crs="EPSG:4326",
    )

    # Construct the query string
    query_string = construct_query_string(**single_filter_dict)

    # Filter the geodataframe by region and by environment
    gdf_filtered = gdf.query(query_string)

    # 2/ Create the regions geodataframe #
    # Unpack the region name
    region = single_filter_dict["REGION"]

    # Load France regions from a GeoJSON file
    regions = gpd.read_file(region_geojson_path)

    # Filter the region geodataframe for the specified region
    selected_region = regions[regions["nom"].str.lower() == region.lower()]
    if selected_region.empty:
        raise KeyError(f"Region '{region}' not found.")

    # 3/ Initialize folium map #
    # Initialize a folium map, centered around the mean location of the waste points
    map_center = [gdf_filtered.geometry.y.mean(), gdf_filtered.geometry.x.mean()]

    # Catch ValueError if the filtered geodataframe contain no rows
    try:
        m = folium.Map(
            location=map_center, zoom_start=5
        )  # Adjust zoom_start as needed for the best initial view

    # Return None if ValueError
    except ValueError as e:
        st.markdown(
            "Il n'y a pas de hotspots pour les valeurs de filtres selectionnés !"
        )
        return

    # 4/ Add the markers #
    # Use MarkerCluster to manage markers if dealing with a large number of points
    marker_cluster = MarkerCluster().add_to(m)

    # Add each waste point as a marker on the folium map
    for _, row in gdf_filtered.iterrows():
        # Define the marker color: green for adopted spots, red for others
        marker_color = "darkgreen" if row["SPOT_A1S"] else "red"
        # Define the icon: check-circle for adopted, info-sign for others
        icon_type = "check-circle" if row["SPOT_A1S"] else "info-sign"

        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            popup=f"Zone: {row['NOM_ZONE']}<br>Date: {row['DATE']}<br>Volume: {row['VOLUME_TOTAL']} litres",
            icon=folium.Icon(color=marker_color, icon=icon_type, prefix="fa"),
        ).add_to(marker_cluster)

    # 5/ Add the region boundary #
    # Add the region boundary to the map for context
    folium.GeoJson(
        selected_region,
        name="Region Boundary",
        style_function=lambda feature: {
            "weight": 2,
            "fillOpacity": 0.1,
        },
    ).add_to(m)

    return m


########################
# Dashboard Main Panel #
########################

tab1, tab2 = st.tabs(
    [
        "Densité des déchets dans zone étudié",
        "Spots Adoptés"
    ]
)

with tab1:

    # Define placeholder widgets for displaying the information
    indicator_col1 = st.container()
    indicator_col2 = st.container()
    indicator_col3 = st.container()

    # Create side-by-side containers for indicators
    indicator_col1, indicator_col2, indicator_col3 = st.columns(3)

    # Call the function with the data and UI elements
    calculate_and_display_metrics(data_zds, indicator_col1, indicator_col2, indicator_col3)

    st.markdown("---")

    left_column, right_column = st.columns([2, 1])

    with left_column:
        st.markdown("### Carte des Densités")
        plot_density_map(data_zds, REGION_GEOJSON_PATH)

    with right_column:
        st.markdown("### Tableau des Densités par Milieu")
        density_table(data_zds)


with tab2:
    # Use the selected filters
    single_filter_dict_3 = scalable_filters_single_select(
        data_zds, ADOPTED_SPOTS_FILTERS_PARAMS, tab2
    )

    st.markdown("### Spots Adoptés")
    m = plot_adopted_waste_spots(data_zds, single_filter_dict_3, REGION_GEOJSON_PATH)
    # Show the adopted spots map on the streamlit tab
    if m:
        folium_static(m)

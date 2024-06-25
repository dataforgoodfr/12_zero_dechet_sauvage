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

# This is a copy of the previous dict, with just the "EPCI" value modified with the
# name of the "COMMUNE_CODE_NOM" column in the data_zds df, in order to trigger the display
# of the "EPCI" level boundaries without an "EPCI" geojson map, knowing that one EPCI is
# made of one or multiple "communes"
NIVEAUX_ADMIN_DICT_ALTERED = {
    "Région": "REGION",
    "Département": "DEPARTEMENT",
    "EPCI": "commune",
    "Commune": "commune",
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

# Root data path for the France administrative levels geojson
NIVEAUX_ADMIN_GEOJSON_ROOT_PATH = (
    "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/1-"
    "exploration-des-donn%C3%A9es/Exploration_visualisation/data/"
)

# Dict containing the path of the administrative levels geojson referenced by the names of these adminitrative levels
NIVEAUX_ADMIN_GEOJSON_PATH_DICT = {
    "Région": f"{NIVEAUX_ADMIN_GEOJSON_ROOT_PATH}regions-avec-outre-mer.geojson",
    "Département": f"{NIVEAUX_ADMIN_GEOJSON_ROOT_PATH}departements-avec-outre-mer.geojson",
    "EPCI": f"{NIVEAUX_ADMIN_GEOJSON_ROOT_PATH}communes-avec-outre-mer.geojson",
    "Commune": f"{NIVEAUX_ADMIN_GEOJSON_ROOT_PATH}communes-avec-outre-mer.geojson",
}

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
    {"filter_col": "TYPE_MILIEU", "filter_message": "Sélectionnez un milieu :"},
    {"filter_col": "ANNEE", "filter_message": "Sélectionnez une année :"},
]

# Params for the density graph filters
DENSITY_FILTERS_PARAMS = [
    {"filter_col": "TYPE_MILIEU", "filter_message": "Sélectionnez un milieu :"},
    {"filter_col": "TYPE_LIEU2", "filter_message": "Sélectionnez un lieu :"},
    {"filter_col": "ANNEE", "filter_message": "Sélectionnez une année :"},
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
# Tab title
st.markdown("""# 🔥 Hotspots : **Quelles sont les zones les plus impactées ?**""")

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
            if isinstance(param, (int, np.int64)):
                # If it's an integer, use integer comparison
                query_sub_string = f"{param_key} == {param}"

            # Check if the parameter value is a list.
            elif isinstance(param, list):
                # Handle list of values for multiselect queries.
                param_values = ", ".join(
                    [
                        f'"{value}"'
                        if not isinstance(value, (int, np.int64))
                        else f"{value}"
                        for value in param
                    ]
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
        sorted_values = sorted(data_zds[column].dropna().unique(), reverse=True)

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


def construct_admin_lvl_filter_list(
    data_zds: pd.DataFrame,
    admin_lvl: str,
    admin_lvl_dict_altered=NIVEAUX_ADMIN_DICT_ALTERED,
) -> list:
    """Create a list of names for a given admin level. This function was created
    in order to trigger the display of the 'EPCI' level boundaries without an
    'EPCI' geojson map, knowing that one EPCI is made of one or multiple 'communes'
    Arguments:
    - data_zds: the dataframe containing waste data and administrative levels columns
    - admin_lvl: the common name of the target administrative level
    Params:
    - admin_lvl_dict_altered: a dict mapping admin levels common names and the names
    of the columns corresponding in the data_zds df"""

    # Unpack the column name of the admin level
    admin_lvl_col_name = admin_lvl_dict_altered[f"{admin_lvl}"]

    # Return the list of uniques administrative names corresponding to the selection made in the home tab
    return list(data_zds[f"{admin_lvl_col_name}"].str.lower().unique())


def construct_admin_lvl_boundaries(
    data_zds: pd.DataFrame, admin_lvl: str, admin_lvl_geojson_path_dict: dict
) -> any:
    """Return a filtered geodataframe with shapes of a target administrative level.
    Arguments:
    - data_zds: the dataframe containing waste data and administrative levels columns
    - admin_lvl: the common name of the target administrative level
    - admin_lvl_geojson_path_dict: a dict mapping administrative levels common
    names and the paths of the geojson administrative levels shapes"""

    # Unpack the admin level geojson path
    admin_lvl_geojson_path = admin_lvl_geojson_path_dict[f"{admin_lvl}"]

    # Unpack the region name
    admin_lvl_names = construct_admin_lvl_filter_list(data_zds, admin_lvl)

    # Load France regions from a GeoJSON file
    admin_lvl_shapes = gpd.read_file(admin_lvl_geojson_path)

    # Filter the region geodataframe for the specified region
    selected_admin_lvl_shapes = admin_lvl_shapes[
        admin_lvl_shapes["nom"].str.lower().isin(admin_lvl_names)
    ]
    if selected_admin_lvl_shapes.empty:
        raise KeyError

    return selected_admin_lvl_shapes


##################
# 1/ Import data #
##################

# Load all regions from the GeoJSON file
# regions = gpd.read_file(REGION_GEOJSON_PATH) # Unused, keep as archive

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
data_zds_correct = data_correct[data_correct["VOLUME_TOTAL"] > 0]

# Filter data_zds for data point which have volume > 0
data_zds = data_zds[data_zds["VOLUME_TOTAL"] > 0]

##################
# 2/ Hotspot tab #
##################

########################################################
# 2.1/ Carte densité de déchets sur les zones étudiées #
########################################################


def calculate_and_display_metrics(data, indicator_col1, indicator_col2, indicator_col3):

    if data.empty:
        st.write("Aucune donnée disponible pour la région sélectionnée.")

    else:
        # Calculate density
        data["DENSITE"] = data["VOLUME_TOTAL"] / data["SURFACE"]
        data = data[
            data["DENSITE"] < 20
        ]  # Remove rows with anomalously high density values

        # Calculate the mean of DENSITE
        mean_density = data["DENSITE"].mean()

        # Check if the result is a float and then apply round
        if isinstance(mean_density, float):
            rounded_mean_density = round(mean_density, 4)
        else:
            # Handle the unexpected type here, maybe set to a default value or raise an error
            rounded_mean_density = 0  # Example default value

        # Display metrics in specified UI containers
        cell1 = indicator_col1.container(border=True)
        cell1.metric("Densité Moyenne :", f"{rounded_mean_density} L/m²")

        # Calculate the mean of VOLUME_TOTAL and check its type
        mean_volume_total = data["VOLUME_TOTAL"].mean()
        if isinstance(mean_volume_total, float):
            rounded_mean_volume_total = round(mean_volume_total, 2)
        else:
            rounded_mean_volume_total = 0  # Example default value

        cell2 = indicator_col2.container(border=True)
        cell2.metric("Volume Moyen :", f"{rounded_mean_volume_total} Litres")

        # Calculate the mean of SURFACE and check its type
        mean_surface = data["SURFACE"].mean()
        if isinstance(mean_surface, float):
            rounded_mean_surface = round(mean_surface, 2)
        else:
            rounded_mean_surface = 0  # Example default value

        cell3 = indicator_col3.container(border=True)
        cell3.metric("Surface Moyenne :", f"{rounded_mean_surface:,} m²")

    return data


# Define the colors representing les différents 'Lieux' et 'Milieux'
couleur = {
    "Littoral (terrestre)": "lightblue",
    "Mer - Océan": "darkblue",
    "Cours d'eau": "cyan",
    "Zone naturelle ou rurale (hors littoral et montagne)": "green",
    "Zone urbaine": "orange",
    "Lagune et étang côtier": "red",
    "Multi-lieux": "pink",
    "Montagne": "grey",
    "Présent au sol (abandonné)": "black",
}

# Function to retrieve the color associated with a given environment type
def couleur_milieu(type):
    return couleur.get(type, "white")  # Returns 'white' if the type is not found


def update_lieu_options(selected_milieu):
    if selected_milieu and selected_milieu != "Sélectionnez un milieu...":
        filtered_data = data_zds[data_zds["TYPE_MILIEU"] == selected_milieu]
        return ["Sélectionnez un lieu..."] + list(
            filtered_data["TYPE_LIEU2"].dropna().unique()
        )
    return ["Sélectionnez un lieu..."]


@st.cache_data
def process_data(data_zds):
    # Filtering data to ensure surface area is not zero
    data_zds = data_zds[data_zds["SURFACE"] > 0]
    # Calculating density and filtering out anomalous values
    data_zds["DENSITE"] = data_zds["VOLUME_TOTAL"] / data_zds["SURFACE"]
    data_zds = data_zds[data_zds["DENSITE"] < 20]
    # Rounding values for better display
    data_zds["DENSITE"] = data_zds["DENSITE"].round(4)
    data_zds["SURFACE_ROND"] = data_zds["SURFACE"].round(2)
    return data_zds


# Zoom from admin level
if NIVEAU_ADMIN == "Commune":
    zoom_admin = 12
elif NIVEAU_ADMIN == "EPCI":
    zoom_admin = 13
elif NIVEAU_ADMIN == "Département":
    zoom_admin = 10
else:
    zoom_admin = 8

# Function to plot a density map
def plot_density_map(data_zds: pd.DataFrame, filtered_data: pd.DataFrame) -> folium.Map:
    # Check if the primary dataset is empty
    if data_zds.empty:
        st.write("Aucune donnée disponible pour la région sélectionnée.")
        return folium.Map(location=[46.6358, 2.5614], zoom_start=5)

    else:
        # Use processed data
        processed_data = process_data(
            filtered_data if not filtered_data.empty else data_zds
        )

        m = folium.Map(
            location=[
                processed_data["LIEU_COORD_GPS_Y"].mean(),
                processed_data["LIEU_COORD_GPS_X"].mean(),
            ],
            zoom_start=zoom_admin,
        )

        # Loop over each row in the DataFrame to place markers
        for index, row in processed_data.iterrows():
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
            color = couleur_milieu(row["TYPE_MILIEU"])
            folium.CircleMarker(
                fg=folium.FeatureGroup(
                    name=lgd_txt.format(txt=["TYPE_MILIEU"], col=color)
                ),
                location=[row["LIEU_COORD_GPS_Y"], row["LIEU_COORD_GPS_X"]],
                radius=np.log(row["DENSITE"] + 1) * 15,
                popup=folium.Popup(popup_html, max_width=300),
                color=color,
                fill=True,
            ).add_to(m)

        folium_static(m)

    return m


# Function for 'milieu' density table
def density_table_milieu(data_zds: pd.DataFrame, filtered_data: pd.DataFrame):

    if data_zds.empty:
        st.write("Aucune donnée disponible pour la région sélectionnée.")

    else:
        # Use filtered data if available; otherwise, use the full dataset
        if filtered_data.empty:
            table_data = data_zds
        else:
            table_data = filtered_data
            # Calculate density
            table_data["DENSITE"] = table_data["VOLUME_TOTAL"] / table_data["SURFACE"]
            # Remove rows with anomalously high density values
            table_data = table_data[table_data["DENSITE"] < 20]

            # Group by 'TYPE_MILIEU', calculate mean density, sort, and round the density
            table_milieu = (
                table_data.groupby("TYPE_MILIEU")["DENSITE"]
                .mean()
                .reset_index()
                .sort_values(by="DENSITE", ascending=False)
            )
            table_milieu["DENSITE"] = table_milieu["DENSITE"].round(4)

            st.dataframe(
                table_milieu,
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
                        max_value=max(table_milieu["DENSITE"]),
                    ),
                },
            )


def density_table_lieu(data_zds: pd.DataFrame, filtered_data: pd.DataFrame):

    if data_zds.empty:
        st.write("Aucune donnée disponible pour la région sélectionnée.")

    else:
        # Use filtered data if available; otherwise, use the full dataset
        if filtered_data.empty:
            table_data = data_zds
        else:
            table_data = filtered_data
            # Calculate density
            table_data["DENSITE"] = table_data["VOLUME_TOTAL"] / table_data["SURFACE"]
            # Remove rows with anomalously high density values
            table_data = table_data[table_data["DENSITE"] < 20]

            # Group by 'TYPE_MILIEU', calculate mean density, sort, and round the density
            table_lieu = (
                table_data.groupby("TYPE_LIEU2")["DENSITE"]
                .mean()
                .reset_index()
                .sort_values(by="DENSITE", ascending=False)
            )
            table_lieu["DENSITE"] = table_lieu["DENSITE"].round(4)

            st.dataframe(
                table_lieu,
                column_order=("TYPE_LIEU2", "DENSITE"),
                hide_index=True,
                width=800,
                column_config={
                    "TYPE_LIEU2": st.column_config.TextColumn(
                        "Milieu",
                    ),
                    "DENSITE": st.column_config.NumberColumn(
                        "Densité (L/m²)",
                        format="%f",
                        min_value=0,
                        max_value=max(table_lieu["DENSITE"]),
                    ),
                },
            )


################################
# 2.1/ Carte des spots adoptés #
################################

# Create the map of the adopted spots
def plot_adopted_waste_spots(
    data_zds: pd.DataFrame,
    multi_filter_dict: dict,
) -> folium.Map:
    """Show a folium innteractive map of adopted spots within a selected region,
    filtered by environments of deposit.
    Arguments:
    - data_zds: The waste dataframe
    - filter_dict: dictionary mapping the name of the column in the waste df and the value you want to filter by
    """
    if data_zds.empty:
        st.write("Aucune donnée disponible pour la région sélectionnée.")

    else:
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
        query_string = construct_query_string(**multi_filter_dict)

        # Filter the geodataframe by region and by environment
        try:
            gdf_filtered = gdf.query(query_string)

        except:
            st.write("Aucune donnée disponible pour les valeurs sélectionnées.")

        # 2/ Create the regions geodataframe #
        selected_admin_lvl = construct_admin_lvl_boundaries(
            data_zds, NIVEAU_ADMIN, NIVEAUX_ADMIN_GEOJSON_PATH_DICT
        )

        # 3/ Initialize folium map #
        # Initialize a folium map, centered around the mean location of the waste points
        map_center = [gdf_filtered.geometry.y.mean(), gdf_filtered.geometry.x.mean()]

        # Catch ValueError if the filtered geodataframe contain no rows
        try:
            m = folium.Map(
                location=map_center
            )  # Adjust zoom_start as needed for the best initial view

        # Return None if ValueError
        except ValueError as e:
            st.markdown(
                "Il n'y a pas de hotspots pour les valeurs de filtres selectionnés !"
            )
            st.markdown(f"{e}")
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

            # Create a folium iframe for the popup window
            iframe = folium.IFrame(
                f"Zone: {row['NOM_ZONE']}<br>Date: {row['DATE']}<br>Volume: {row['VOLUME_TOTAL']} litres<br>Structure: {row['NOM_STRUCTURE']}"
            )

            # Create the popup window based on the iframe
            popup = folium.Popup(iframe, min_width=200, max_width=300)

            folium.Marker(
                location=[row.geometry.y, row.geometry.x],
                popup=popup,
                icon=folium.Icon(color=marker_color, icon=icon_type, prefix="fa"),
            ).add_to(marker_cluster)

        # 5/ Add the region boundary #
        # Add the region boundary to the map for context
        folium.GeoJson(
            selected_admin_lvl,
            name="Region Boundary",
            style_function=lambda feature: {
                "weight": 2,
                "fillOpacity": 0.1,
            },
        ).add_to(m)

        return m


def create_contributors_table(data_zds: pd.DataFrame, multi_filter_dict: dict) -> None:
    """Create and show a streamlit table of the number of collects by contributors,
    given a set of filters choosen by the user.
    Arguments:
    - data_zds: The waste dataframe
    - filter_dict: dictionary mapping the name of the column in the waste df and the value you want to filter by"""

    # Handle case if there is no data
    if data_zds.empty:
        st.write("Aucune donnée disponible pour la région sélectionnée.")

    else:
        # Construct the query string and filter the table of contributors given the user input
        query_string = construct_query_string(**multi_filter_dict)
        data_zds_filtered = data_zds.query(query_string)

        # Create the table (pandas serie) of contributors
        contributors_table = (
            data_zds_filtered.groupby("NOM_STRUCTURE")
            .count()
            .loc[:, "ID_RELEVE"]
            .sort_values(ascending=False)
        )

        # Create and show the table in streamlit
        st.dataframe(
            contributors_table,
            width=800,
            column_config={
                "NOM_STRUCTURE": st.column_config.TextColumn("Structure"),
                "ID_RELEVE": st.column_config.NumberColumn("Nombre de ramassages"),
            },
        )


########################
# Dashboard Main Panel #
########################

tab1, tab2 = st.tabs(["Densité des déchets dans zone étudié🔍", "Spots Adoptés📍"])

with tab1:

    # Define placeholder widgets for displaying the information
    indicator_col1 = st.container()
    indicator_col2 = st.container()
    indicator_col3 = st.container()

    # Create side-by-side containers for indicators
    indicator_col1, indicator_col2, indicator_col3 = st.columns(3)

    # Call the function with the data and UI elements
    calculate_and_display_metrics(
        data_zds_correct, indicator_col1, indicator_col2, indicator_col3
    )

    st.markdown("---")

    left_column, right_column = st.columns([2, 2])

    with left_column:
        # Add a default "Select a milieu..." option
        selected_milieu = st.selectbox(
            "Sélectionnez un milieu:",
            ["Sélectionnez un milieu..."]
            + list(pd.unique(data_zds_correct["TYPE_MILIEU"])),
        )
    with right_column:
        # Update lieu options based on selected milieu
        lieu_options = update_lieu_options(selected_milieu)
        selected_lieu = st.selectbox("Sélectionnez un lieu:", lieu_options)

    # Place the map centrally by using a wider column for the map and narrower ones on the sides
    col1, map_col, col3 = st.columns([4, 10, 1])  # Adjust column ratios as needed

    with map_col:
        st.markdown("### Carte des Densités")
        if (
            selected_milieu != "Sélectionnez un milieu..."
            and selected_lieu != "Sélectionnez un lieu..."
        ):
            filtered_data = data_zds_correct[
                (data_zds_correct["TYPE_MILIEU"] == selected_milieu)
                & (data_zds_correct["TYPE_LIEU2"] == selected_lieu)
            ]
            plot_density_map(data_zds_correct, filtered_data)
        else:
            plot_density_map(
                data_zds_correct, data_zds_correct
            )  # Show all data by default

    col1, col2, col3 = st.columns([3, 3, 2])

    with col1:
        st.markdown("#### Tableau des Densités par Milieu")
        if (
            selected_milieu != "Sélectionnez un milieu..."
            and selected_lieu != "Sélectionnez un lieu..."
        ):
            filtered_data = data_zds_correct[
                (data_zds_correct["TYPE_MILIEU"] == selected_milieu)
                & (data_zds_correct["TYPE_LIEU2"] == selected_lieu)
            ]
            density_table_milieu(data_zds_correct, filtered_data)
        else:
            density_table_milieu(data_zds_correct, data_zds_correct)

    with col2:
        st.markdown("#### Tableau des Densités par Lieu")
        if (
            selected_milieu != "Sélectionnez un milieu..."
            and selected_lieu != "Sélectionnez un lieu..."
        ):
            filtered_data = data_zds_correct[
                (data_zds_correct["TYPE_MILIEU"] == selected_milieu)
                & (data_zds_correct["TYPE_LIEU2"] == selected_lieu)
            ]
            density_table_lieu(data_zds_correct, filtered_data)
        else:
            density_table_lieu(data_zds_correct, data_zds_correct)

    with col3:
        with st.expander("###### Notice ℹ️", expanded=True):
            st.write(
                """
                    **Milieu** désigne de grands types d'environnements comme le Littoral,
                    les Cours d'eau ou la Montagne.\n
                    Chaque Milieu est ensuite divisé en
                    **Lieux** plus spécifiques. Par exemple, sous le Milieu Littoral,
                    on trouve des Lieux comme les Plages, les Roches, les Digues, ou les Parkings.
                    """
            )

with tab2:
    # Use the selected filters
    single_filter_dict_3 = scalable_filters_multi_select(
        data_zds, filters_params=ADOPTED_SPOTS_FILTERS_PARAMS, base_key=tab2
    )

    # Construct the adopted waste spots map
    m = plot_adopted_waste_spots(data_zds, single_filter_dict_3)

    # Construct wo columns, one for the spots map the other for the tab of structures
    left_column, right_column = st.columns([2, 1])

    # Show the adopted spots map on the streamlit tab
    with left_column:
        if m:
            st.markdown("### Carte des spots adoptés")
            folium_static(m)

    # Show the contributors table on the second column
    with right_column:
        st.markdown("### Tableau du nombre de ramassages par acteur")
        create_contributors_table(data_zds, single_filter_dict_3)

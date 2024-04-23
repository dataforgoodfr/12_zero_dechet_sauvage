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
    "Département": "DEP_CODE_NOM",
    "EPCI": "COMMUNE_CODE_NOM",
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
    return data_zds[f"{admin_lvl_col_name}"].str.lower().unique().to_list()


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
data_zds = data_correct[data_correct["VOLUME_TOTAL"] > 0]

##################
# 2/ Hotspot tab #
##################

# Tab title
st.markdown("""# 🔥 Hotspots : **Quelles sont les zones les plus impactées ?**""")


########################################################
# 2.1/ Carte densité de déchets sur les zones étudiées #
########################################################
# à faire!

####################################################################################
# 2.2/ Tableaux de la densité par milieu et lieu de déchets sur les zones étudiées #
####################################################################################


def density_lieu(data_zds: pd.DataFrame, multi_filter_dict: dict):
    """
    Calculate and display the density of waste by type of location ('LIEU') for a selected region.
    """

    # Get the selected region from filter_dict
    selected_regions = multi_filter_dict.get("REGION", [])

    if selected_regions is not None:
        # Filter data for selected region
        data_selected_region = data_zds[data_zds["LIEU_REGION"].isin(selected_regions)]

        # Calculate waste volume sum for each 'LIEU'
        volume_total_lieu = (
            data_selected_region.groupby("TYPE_LIEU2")["VOLUME_TOTAL"]
            .sum()
            .reset_index()
        )

        # Remove duplicate data and calculate SURFACE total
        data_unique = data_selected_region.drop_duplicates(subset=["LIEU_COORD_GPS"])
        surface_total_lieu = (
            data_unique.groupby("TYPE_LIEU2")["SURFACE"].sum().reset_index()
        )

        # Merge volume and surface data for 'LIEU', calculate density, and sort
        data_lieu = pd.merge(volume_total_lieu, surface_total_lieu, on="TYPE_LIEU2")
        data_lieu["DENSITE_LIEU"] = (
            data_lieu["VOLUME_TOTAL"] / data_lieu["SURFACE"]
        ).round(5)
        data_lieu_sorted = data_lieu.sort_values(by="DENSITE_LIEU", ascending=False)

        # Display sorted DataFrame with specific configuration for 'data_lieu_sorted'
        lieu = st.markdown("##### Densité des déchets par type de lieu (L/m2)")
        st.dataframe(
            data_lieu_sorted,
            column_order=("TYPE_LIEU2", "DENSITE_LIEU"),
            hide_index=True,
            width=None,
            column_config={
                "TYPE_LIEU2": st.column_config.TextColumn(
                    "Lieu",
                ),
                "DENSITE_LIEU": st.column_config.ProgressColumn(
                    "Densité",
                    format="%f",
                    min_value=0,
                    max_value=max(data_lieu_sorted["DENSITE_LIEU"]),
                ),
            },
        )

        return lieu


def density_milieu(data_zds: pd.DataFrame, multi_filter_dict: dict):
    """
    Calculate and display the density of waste by type of location ('MILIEU') for a selected region.
    """
    # Get the selected region from filter_dict
    selected_regions = multi_filter_dict.get("REGION", [])

    if selected_regions is not None:
        # Filter data for selected region
        data_selected_region = data_zds[data_zds["LIEU_REGION"].isin(selected_regions)]

        # Calculate waste volume sum for each 'MILIEU'
        volume_total_milieu = (
            data_selected_region.groupby("TYPE_MILIEU")["VOLUME_TOTAL"]
            .sum()
            .reset_index()
        )

        # Remove duplicate data and calculate SURFACE total
        data_unique = data_selected_region.drop_duplicates(subset=["LIEU_COORD_GPS"])
        surface_total_milieu = (
            data_unique.groupby("TYPE_MILIEU")["SURFACE"].sum().reset_index()
        )

        # Merge volume and surface data for 'MILIEU', calculate density, and sort
        data_milieu = pd.merge(
            volume_total_milieu, surface_total_milieu, on="TYPE_MILIEU"
        )
        data_milieu["DENSITE_MILIEU"] = (
            data_milieu["VOLUME_TOTAL"] / data_milieu["SURFACE"]
        ).round(5)
        data_milieu_sorted = data_milieu.sort_values(
            by="DENSITE_MILIEU", ascending=False
        )

        # Display sorted DataFrame with specific configuration for 'data_milieu_sorted'
        milieu = st.markdown("##### Densité des déchets par type de milieu (L/m2)")
        st.dataframe(
            data_milieu_sorted,
            column_order=("TYPE_MILIEU", "DENSITE_MILIEU"),
            hide_index=True,
            width=None,
            column_config={
                "TYPE_MILIEU": st.column_config.TextColumn(
                    "Milieu",
                ),
                "DENSITE_MILIEU": st.column_config.ProgressColumn(
                    "Densité",
                    format="%f",
                    min_value=0,
                    max_value=max(data_milieu_sorted["DENSITE_MILIEU"]),
                ),
            },
        )

        return milieu


######################################################
# 2.3/ Carte choropleth densité de déchets en France #
######################################################


def make_density_choropleth(data_zds, region_geojson_path):
    # Load all regions from the GeoJSON file
    regions_geojson = requests.get(region_geojson_path).json()

    # Extract region names from GeoJSON for later comparison
    regions_from_geojson = [
        feature["properties"]["nom"] for feature in regions_geojson["features"]
    ]

    # Create a DataFrame from the GeoJSON region names
    regions_df = pd.DataFrame(regions_from_geojson, columns=["nom"])

    # Data preparation
    # Calculate the total VOLUME_TOTAL for each region without removing duplicate data
    volume_total_sums = (
        data_zds.groupby("LIEU_REGION")["VOLUME_TOTAL"].sum().reset_index()
    )

    # Merge the waste data and the geographical data
    volume_total_sums = pd.merge(
        regions_df, volume_total_sums, left_on="nom", right_on="LIEU_REGION", how="left"
    )

    # Identify regions with no available data
    regions_no_data = volume_total_sums[volume_total_sums["VOLUME_TOTAL"].isna()][
        "nom"
    ].tolist()
    if regions_no_data:
        st.info(
            f"Aucune donnée disponible pour les régions suivantes : {', '.join(regions_no_data)}",
            icon="⚠️",
        )

    # Drop rows containing NaN to avoid errors in the choropleth
    volume_total_sums.dropna(inplace=True)

    # Remove duplicate data and calculate SURFACE total
    data_unique = data_zds.drop_duplicates(subset=["LIEU_COORD_GPS"])
    surface_total_sums = (
        data_unique.groupby("LIEU_REGION")["SURFACE"].sum().reset_index()
    )

    # Combine two datasets and calculate DENSITE
    data_choropleth_sums = pd.merge(
        volume_total_sums, surface_total_sums, on="LIEU_REGION"
    )
    data_choropleth_sums["DENSITE"] = (
        data_choropleth_sums["VOLUME_TOTAL"] / data_choropleth_sums["SURFACE"]
    )

    # Set bins for the choropleth
    min_density = data_choropleth_sums["DENSITE"].min()
    max_density = data_choropleth_sums["DENSITE"].max()

    # Create the choropleth map using Plotly Express
    choropleth = px.choropleth(
        data_choropleth_sums,
        geojson=regions_geojson,
        featureidkey="properties.nom",
        locations="LIEU_REGION",
        color="DENSITE",
        color_continuous_scale="Reds",
        range_color=(min_density, max_density),  # set range using log scale
        labels={"DENSITE": "Densité de Déchets(L/m2)"},
    )

    # Update layout to fit the map to the boundaries of the GeoJSON
    choropleth.update_layout(
        geo=dict(fitbounds="locations", visible=False), margin=dict(l=0, r=0, t=0, b=0)
    )

    return choropleth


############################################################
# 2.1/ Line chart de l'évolution de la densité des déchets #
#  par lieu et par milieu au fil des années spots adoptés  #
############################################################


def line_chart_lieu(data_zds: pd.DataFrame, multi_filter_dict: dict):
    # Get the selected region and milieu from the filter dictionary
    selected_regions = multi_filter_dict.get("REGION", [])
    selected_lieu = multi_filter_dict.get("TYPE_LIEU2", [])

    # Ensure that at least one region is selected
    if not selected_regions:
        st.error("Aucune région sélectionnée. Veuillez préciser une région.")
        return

    # Filter data for the selected region
    data_selected_region = data_zds[data_zds["LIEU_REGION"].isin(selected_regions)]
    if data_selected_region.empty:
        st.warning(
            f"Aucune donnée disponible pour la région sélectionnée : {selected_regions}"
        )
        return

    # Further filter data for the selected milieus
    data_selected_lieu = (
        data_selected_region[data_selected_region["TYPE_LIEU2"].isin(selected_lieu)]
        if selected_lieu
        else data_selected_region
    )

    # Check if there is any data left after filtering by milieu
    if data_selected_lieu.empty:
        st.warning("Aucune donnée disponible pour le lieu sélectionné.")
        return

    # Calculate waste volume sum for each 'LIEU' by 'ANNEE'
    volume_total_annee = (
        data_selected_lieu.groupby(["TYPE_LIEU2", "ANNEE"])["VOLUME_TOTAL"]
        .sum()
        .reset_index()
    )

    # Remove duplicate data and calculate SURFACE total
    data_unique = data_selected_lieu.drop_duplicates(subset=["LIEU_COORD_GPS"])
    surface_total_annee = (
        data_unique.groupby(["TYPE_LIEU2", "ANNEE"])["SURFACE"].sum().reset_index()
    )

    # Merge volume and surface data for 'MILIEU', calculate density, and sort
    data_lieu = pd.merge(
        volume_total_annee, surface_total_annee, on=["TYPE_LIEU2", "ANNEE"]
    )
    if data_lieu.empty:
        st.warning(
            "Aucune donnée superposée pour les calculs de volume et de surface pour les lieux sélectionnés."
        )
        return

    data_lieu["DENSITE_LIEU"] = (
        data_lieu["VOLUME_TOTAL"] / data_lieu["SURFACE"]
    ).round(5)
    data_lieu_sorted = data_lieu.sort_values(by="ANNEE", ascending=False)

    # Create the plot
    fig = go.Figure()
    for type_lieu in data_lieu_sorted["TYPE_LIEU2"].unique():
        df_plot = data_lieu_sorted[data_lieu_sorted["TYPE_LIEU2"] == type_lieu]
        fig.add_trace(
            go.Scatter(
                x=df_plot["ANNEE"],
                y=df_plot["DENSITE_LIEU"],
                mode="lines+markers",
                name=type_lieu,
            )
        )

    # Update plot layout
    fig.update_layout(
        title=f"Densité des déchets par type de lieu",
        xaxis_title="Année",
        yaxis_title="Densité L/m2",
        legend_title="Type de lieu",
    )

    st.plotly_chart(fig)


def line_chart_milieu(data_zds: pd.DataFrame, multi_filter_dict: dict):
    # Get the selected region and milieu from the filter dictionary
    selected_regions = multi_filter_dict.get("REGION", [])
    selected_milieu = multi_filter_dict.get("TYPE_MILIEU", [])

    # Ensure that at least one region is selected
    if not selected_regions:
        st.error("Aucune région sélectionnée. Veuillez préciser une région.")
        return

    # Filter data for the selected region
    data_selected_region = data_zds[data_zds["LIEU_REGION"].isin(selected_regions)]
    if data_selected_region.empty:
        st.warning(
            f"Aucune donnée disponible pour la région sélectionnée : {selected_regions}"
        )
        return

    # Further filter data for the selected milieus
    data_selected_milieu = (
        data_selected_region[data_selected_region["TYPE_MILIEU"].isin(selected_milieu)]
        if selected_milieu
        else data_selected_region
    )

    # Check if there is any data left after filtering by milieu
    if data_selected_milieu.empty:
        st.warning("Aucune donnée disponible pour le milieu sélectionné.")
        return

    # Calculate waste volume sum for each 'MILIEU' by 'ANNEE'
    volume_total_annee = (
        data_selected_milieu.groupby(["TYPE_MILIEU", "ANNEE"])["VOLUME_TOTAL"]
        .sum()
        .reset_index()
    )

    # Remove duplicate data and calculate SURFACE total
    data_unique = data_selected_milieu.drop_duplicates(subset=["LIEU_COORD_GPS"])
    surface_total_annee = (
        data_unique.groupby(["TYPE_MILIEU", "ANNEE"])["SURFACE"].sum().reset_index()
    )

    # Merge volume and surface data for 'MILIEU', calculate density, and sort
    data_milieu = pd.merge(
        volume_total_annee, surface_total_annee, on=["TYPE_MILIEU", "ANNEE"]
    )
    if data_milieu.empty:
        st.warning(
            "Aucune donnée superposée pour les calculs de volume et de surface pour les milieux sélectionnés."
        )
        return

    data_milieu["DENSITE_MILIEU"] = (
        data_milieu["VOLUME_TOTAL"] / data_milieu["SURFACE"]
    ).round(5)
    data_milieu_sorted = data_milieu.sort_values(by="ANNEE", ascending=False)

    # Create the plot
    fig = go.Figure()
    for type_milieu in data_milieu_sorted["TYPE_MILIEU"].unique():
        df_plot = data_milieu_sorted[data_milieu_sorted["TYPE_MILIEU"] == type_milieu]
        fig.add_trace(
            go.Scatter(
                x=df_plot["ANNEE"],
                y=df_plot["DENSITE_MILIEU"],
                mode="lines+markers",
                name=type_milieu,
            )
        )

    # Update plot layout
    fig.update_layout(
        title=f"Densité des déchets par type de milieu",
        xaxis_title="Année",
        yaxis_title="Densité L/m2",
        legend_title="Type de milieu",
    )

    st.plotly_chart(fig)


################################
# 2.1/ Carte des spots adoptés #
################################

# Create the map of the adopted spots
def plot_adopted_waste_spots(
    data_zds: pd.DataFrame,
    single_filter_dict: dict,
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

    # Convert ANNEE values to integers
    if "ANNEE" in single_filter_dict:
        single_filter_dict["ANNEE"] = int(single_filter_dict["ANNEE"])

    # Construct the query string
    query_string = construct_query_string(**single_filter_dict)

    # Filter the geodataframe by region and by environment
    gdf_filtered = gdf.query(query_string)

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
        selected_admin_lvl,
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

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Densité des déchets dans zone étudié",
        "Évolution de la densité au fil du temps",
        "Spots Adoptés",
        "Aperçu à travers la France",
    ]
)

with tab1:

    # Select only the filters for 'REGION' and 'ANNEE'
    selected_filters_1 = [
        f for f in DENSITY_FILTERS_PARAMS if f["filter_col"] in ["REGION", "ANNEE"]
    ]

    # Use the selected filters for multi-select
    multi_filter_dict_1 = scalable_filters_multi_select(
        data_zds, selected_filters_1, tab1
    )

    col = st.columns((4, 4, 2), gap="medium")

    # Construct the map
    with col[0]:
        density_lieu(data_zds, multi_filter_dict_1)

    with col[1]:
        density_milieu(data_zds, multi_filter_dict_1)

    with col[2]:
        with st.expander("Notice ℹ️", expanded=True):
            st.write(
                """
                Explication des diffférences entre Lieu et Milieu
            """
            )

with tab2:
    # Select only the filters for 'REGION' and 'ANNEE'
    selected_filters_2 = [
        f
        for f in DENSITY_FILTERS_PARAMS
        if f["filter_col"] in ["REGION", "TYPE_LIEU2", "TYPE_MILIEU"]
    ]

    # Use the selected filters for multi-select
    multi_filter_dict_2 = scalable_filters_multi_select(
        data_zds, selected_filters_2, tab2
    )

    col = st.columns((7, 7), gap="medium")

    with col[0]:
        line_chart_lieu(data_zds, multi_filter_dict_2)

    with col[1]:
        line_chart_milieu(data_zds, multi_filter_dict_2)

with tab3:
    # Use the selected filters
    single_filter_dict_3 = scalable_filters_single_select(
        data_zds, ADOPTED_SPOTS_FILTERS_PARAMS, tab3
    )

    st.markdown("### Spots Adoptés")
    m = plot_adopted_waste_spots(data_zds, single_filter_dict_3)
    # Show the adopted spots map on the streamlit tab
    if m:
        folium_static(m)

with tab4:
    st.markdown("### Densité des déchets en France")
    choropleth = make_density_choropleth(
        data_zds, NIVEAUX_ADMIN_GEOJSON_PATH_DICT["Région"]
    )
    st.plotly_chart(choropleth, use_container_width=True)

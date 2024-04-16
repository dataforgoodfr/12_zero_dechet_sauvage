import streamlit as st

# import altair as alt # Unused for now
import pandas as pd
import geopandas as gpd

# import duckdb # Unused for now
import folium
from folium.plugins import MarkerCluster

# To show folium maps on streamlit
from streamlit_folium import folium_static, st_folium


######################################
# 0/ Parameters for the hotspots tab #
######################################

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
    "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/1-"
    "exploration-des-donn%C3%A9es/Exploration_visualisation/regions"
    "-avec-outre-mer.geojson"
)

# Params for the adopted spots map filters
ADOPTED_SPOTS_FILTERS_PARAMS = [
    {
        "filter_col": "REGION",
        "filter_message": "Seléctionnez une région (par défaut votre région) :",
    },
    {"filter_col": "TYPE_MILIEU", "filter_message": "Seléctionnez un milieu :"},
]

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
            query_sub_string = f'{param_key} == "{param}"'

            # Add to the query string
            query_string += f"{query_sub_string}{bound_word}"

    # Strip any remaining " and " at the end of the query string
    return query_string.strip(bound_word)


def scalable_filters(
    data_zds: pd.DataFrame, filters_params=ADOPTED_SPOTS_FILTERS_PARAMS
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

        # Set the list of choices
        x = data_zds[column].unique()

        # Create the streamlit select box
        s = columns[i].selectbox(message, x)

        # Show the select box on screen
        columns[i].write(s)

        # Fill the filter dict
        filter_dict[column] = s

    return filter_dict


##################
# 1/ Import data #
##################

# nb dechets : Unused for now
df_nb_dechets = pd.read_csv(NB_DECHETS_PATH)

# data_zds : main source of data for the hotspots tab
data_zds = pd.read_csv(DATA_ZDS_PATH)


##################
# 2/ Hotspot tab #
##################

# Tab title
st.markdown("""# 🔥 Hotspots : **Quelles sont les zones les plus impactées ?**""")


################################
# 2.1/ Carte des spots adoptés #
################################

# Create the filter dict for the adopted spots map and the streamlit filter boxes
filter_dict = scalable_filters(data_zds)

# Create the map of the adopted spots
def plot_adopted_waste_spots(
    data_zds: pd.DataFrame,
    filter_dict: dict,
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
    query_string = construct_query_string(**filter_dict)

    # Filter the geodataframe by region and by environment
    gdf_filtered = gdf.query(query_string)

    # 2/ Create the regions geodataframe #

    # Unpack the region name
    region = filter_dict["REGION"]

    # Load France regions from a GeoJSON file
    regions = gpd.read_file(region_geojson_path)
    regions = regions.loc[regions["nom"] == region, :]

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


# Construct the map
m = plot_adopted_waste_spots(data_zds, filter_dict, REGION_GEOJSON_PATH)

# Show the adopted spots map on the streamlit tab
if m:
    folium_static(m)


########################################################
# 2.1/ Carte densité de déchets sur les zones étudiées #
########################################################

import streamlit as st

# import altair as alt # Unused for now
import pandas as pd
import numpy as np
import geopandas as gpd

# import duckdb # Unused for now

# import for choropleth map
import requests
import plotly.express as px


# To show folium maps on streamlit
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static, st_folium

######################
# Page configuration #
######################
st.set_page_config(
    page_title="Hotspots",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
        }
    )

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
        "filter_message": "Sélectionnez une région (par défaut votre région) :"
        },
    {
        "filter_col": "TYPE_MILIEU", "filter_message": "Sélectionnez un milieu :"
        },
    {
        "filter_col":"ANNEE", "filter_message": "Sélectionnez une année :"
        }
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
        if param is not None:
            # Check if the parameter value is of type int
            if isinstance(param, int):
                # If it's an integer, use integer comparison
                query_sub_string = f'{param_key} == {param}'
            else:
                # If it's not an integer, treat it as a string
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

       # Sort the unique values of the column in ascending order
        sorted_values = sorted(data_zds[column].unique(), reverse=True)

        # Create the streamlit select box with sorted values
        s = columns[i].selectbox(message, sorted_values)

        # Show the select box on screen
        columns[i].write(s)

        # Fill the filter dict
        filter_dict[column] = s

    return filter_dict


##################
# 1/ Import data #
##################

# Load all regions from the GeoJSON file
regions = gpd.read_file(REGION_GEOJSON_PATH)

# nb dechets : Unused for now
df_nb_dechets = pd.read_csv(NB_DECHETS_PATH)

# data_zds : main source of data for the hotspots tab
data_zds = pd.read_csv(DATA_ZDS_PATH)

# spot:
#spot = pd.read_excel(DATA_SPOT)

# correction : corrected data for density map
#correction = pd.read_excel(CORRECTION)

# Fusion and correction
#data_correct = pd.merge(data_zds, correction, on='ID_RELEVE', how='left')
#data_correct = data_correct[data_correct['SURFACE_OK'] == 'OUI']
#data_zds = data_correct[data_correct['VOLUME_TOTAL'] > 0]

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
    print("Filter Dictionary:", filter_dict)  # Check the filter dictionary

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
    if "ANNEE" in filter_dict:
        filter_dict["ANNEE"] = int(filter_dict["ANNEE"])

    # Construct the query string
    query_string = construct_query_string(**filter_dict)
    print("Query String:", query_string)  # Check the constructed query string

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



####################################################################################
# 2.1/ Tableaux de la densité par milieu et lieu de déchets sur les zones étudiées #
####################################################################################

def data_density_lieu_preparation(data):

    # Calculate waste volume sum for each 'LIEU'
    volume_total_lieu = data.groupby('TYPE_LIEU2')['VOLUME_TOTAL'].sum().reset_index()

    # Remove duplicate data and calculate SURFACE total
    data_unique = data.drop_duplicates(subset=['LIEU_COORD_GPS'])
    surface_total_lieu = data_unique.groupby('TYPE_LIEU2')['SURFACE'].sum().reset_index()

    # Merge volume and surface data for 'LIEU', calculate density, and sort
    data_lieu = pd.merge(volume_total_lieu, surface_total_lieu, on='TYPE_LIEU2')
    data_lieu['DENSITE_LIEU'] = (data_lieu['VOLUME_TOTAL'] / data_lieu['SURFACE']).round(5)
    data_lieu_sorted = data_lieu.sort_values(by="DENSITE_LIEU", ascending=False)

    return data_lieu_sorted

def data_density_milieu_preparation(data):

    # Calculate waste volume sum for each 'MILIEU'
    volume_total_milieu = data.groupby('TYPE_MILIEU')['VOLUME_TOTAL'].sum().reset_index()

    # Remove duplicate data and calculate SURFACE total
    data_unique = data.drop_duplicates(subset=['LIEU_COORD_GPS'])
    surface_total_milieu = data_unique.groupby('TYPE_MILIEU')['SURFACE'].sum().reset_index()

    # Merge volume and surface data for 'MILIEU', calculate density, and sort
    data_milieu = pd.merge(volume_total_milieu, surface_total_milieu, on='TYPE_MILIEU')
    data_milieu['DENSITE_MILIEU'] = (data_milieu['VOLUME_TOTAL'] / data_milieu['SURFACE']).round(5)
    data_milieu_sorted = data_milieu.sort_values(by="DENSITE_MILIEU", ascending=False)

    return data_milieu_sorted

def density_lieu(data_zds: pd.DataFrame, filter_dict: dict):
    """
    Calculate and display the density of waste by type of location ('LIEU') for a selected region.
    """
    # Get the selected region from filter_dict
    selected_region = filter_dict.get("REGION", None)

    if selected_region is not None:
        # Filter data for selected region
        data_selected_region = data_zds[data_zds['LIEU_REGION'] == selected_region]

        # Apply data preparation function
        data_lieu_sorted = data_density_lieu_preparation(data_selected_region)

        # Display sorted DataFrame with specific configuration for 'data_lieu_sorted'
        lieu = st.markdown('##### Densité des déchets par type de lieu (L/m2)')
        st.dataframe(data_lieu_sorted,
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
                            max_value=max(data_lieu_sorted['DENSITE_LIEU']),
                        )}
                    )

        return lieu



def density_milieu(data_zds: pd.DataFrame, filter_dict: dict):
    """
    Calculate and display the density of waste by type of location ('MILIEU') for a selected region.
    """
    # Get the selected region from filter_dict
    selected_region = filter_dict.get("REGION", None)

    if selected_region is not None:
        # Filter data for selected region
        data_selected_region = data_zds[data_zds['LIEU_REGION'] == selected_region]

        # Apply data preparation function
        data_milieu_sorted = data_density_milieu_preparation(data_selected_region)

        # Display sorted DataFrame with specific configuration for 'data_milieu_sorted'
        milieu = st.markdown('##### Densité des déchets par type de milieu (L/m2)')
        st.dataframe(data_milieu_sorted,
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
                            max_value=max(data_milieu_sorted['DENSITE_MILIEU']),
                        )}
                    )

        return milieu


########################################################
# 2.2/ Carte densité de déchets sur les zones étudiées #
########################################################




######################################################
# 2.3/ Carte choropleth densité de déchets en France #
######################################################

def make_density_choropleth(data_zds, region_geojson_path):
    # Load all regions from the GeoJSON file
    regions_geojson = requests.get(region_geojson_path).json()

    # Data preparation
    # Calculate the total VOLUME_TOTAL for each region without removing duplicate data
    volume_total_sums = data_zds.groupby('LIEU_REGION')['VOLUME_TOTAL'].sum().reset_index()

    # Merge the waste data and the geographical data
    volume_total_sums = pd.merge(regions, volume_total_sums, left_on='nom', right_on='LIEU_REGION', how='left')

    # Remove rows containing NaN
    volume_total_sums = volume_total_sums.dropna()

    # Remove duplicate data and calculate SURFACE total
    data_unique = data_zds.drop_duplicates(subset=['LIEU_COORD_GPS'])
    surface_total_sums = data_unique.groupby('LIEU_REGION')['SURFACE'].sum().reset_index()

    # Combine two datasets and calculate DENSITE
    data_choropleth_sums = pd.merge(volume_total_sums, surface_total_sums, on='LIEU_REGION')
    data_choropleth_sums['DENSITE'] = data_choropleth_sums['VOLUME_TOTAL'] / data_choropleth_sums['SURFACE']

    # Set bins for the choropleth
    min_density = data_choropleth_sums['DENSITE'].min()
    max_density = data_choropleth_sums['DENSITE'].max()

    # Create the choropleth map using Plotly Express
    choropleth = px.choropleth(
        data_choropleth_sums,
        geojson=regions_geojson,
        featureidkey="properties.nom",
        locations='LIEU_REGION',
        color='DENSITE',
        color_continuous_scale='Reds',
        range_color=(min_density, max_density), # set range using log scale
        labels={'DENSITE': 'Densité de Déchets(L/m2)'}
    )

    # Update layout to fit the map to the boundaries of the GeoJSON
    choropleth.update_layout(
        geo=dict(
            fitbounds="locations",
            visible=False
        ),
        margin=dict(l=0, r=0, t=0, b=0)
    )


    return choropleth

########################
# Dashboard Main Panel #
########################


st.markdown('### Spots Adoptés')
m = plot_adopted_waste_spots(data_zds, filter_dict, REGION_GEOJSON_PATH)
# Show the adopted spots map on the streamlit tab
if m:
    folium_static(m)

col = st.columns((4, 4, 2), gap='medium')

# Construct the map
with col[0]:

    density_lieu(data_zds, filter_dict)

with col[1]:

    density_milieu(data_zds, filter_dict)

with col[2]:
    with st.expander('Notice ℹ️', expanded=True):
        st.write('''
            Explication des diffférences entre Lieu et Milieu
            ''')

st.markdown('### Densité des déchets en France')
choropleth = make_density_choropleth(data_zds, REGION_GEOJSON_PATH)
st.plotly_chart(choropleth, use_container_width=True)

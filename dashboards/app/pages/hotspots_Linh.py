import streamlit as st

# import altair as alt # Unused for now
import pandas as pd
import numpy as np
import geopandas as gpd

# import duckdb # Unused for now
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
    initial_sidebar_state="expanded")

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
        "filter_message": "Sélectionnez une région:\n(par défaut votre région)",
    },
    {"filter_col": "TYPE_MILIEU", "filter_message": "Sélectionnez un milieu :"},
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


def scalable_filters(data_zds: pd.DataFrame, filters_params=ADOPTED_SPOTS_FILTERS_PARAMS) -> dict:
    """Create Streamlit select box filters in the sidebar as specified by the filters_params list.
    Create and return the filter dict used to filter the hotspots maps accordingly."""

    filter_dict = {}

    with st.sidebar:
        for filter_params in filters_params:
            column = filter_params['filter_col']
            message = filter_params['filter_message']

            # Check if the message contains a newline character
            if '\n' in message:
                # Split the message at the newline character
                main_message, sub_message = message.split('\n')
                st.markdown(f"**{main_message}**")  # Display the main part as bold text
                st.caption(sub_message)  # Display the secondary part as caption
            else:
                st.markdown(f"**{message}**")  # If no newline, display the message as bold text

            # No newline in the selectbox label, so we pass only the main_message
            selected_value = st.selectbox("", data_zds[column].unique())

            filter_dict[column] = selected_value

    return filter_dict


##############################
# 1/ Import and prepare data #
##############################

# Load all regions from the GeoJSON file
regions = gpd.read_file(REGION_GEOJSON_PATH)

# nb dechets : Unused for now
df_nb_dechets = pd.read_csv(NB_DECHETS_PATH)

# data_zds : main source of data for the hotspots tab
data_zds = pd.read_csv(DATA_ZDS_PATH)

# correction : corrected data for density map
correction = pd.read_excel(CORRECTION)

# spot:
spot = pd.read_excel(DATA_SPOT)

# Fusion and correction
data_correct = pd.merge(data_zds, correction, on='ID_RELEVE', how='left')
data_correct = data_correct[data_correct['SURFACE_OK'] == 'OUI']
data_zds = data_correct[data_correct['VOLUME_TOTAL'] > 0]

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


########################################################
# 2.1/ Carte densité de déchets sur les zones étudiées #
########################################################



########################################################
# 2.2/ Carte choropleth de la densité de déchets       #
########################################################

def plot_waste_density_choropleth(
    data_zds: pd.DataFrame,
    region_geojson_path: str,
) -> folium.Map:

    # Load all regions from the GeoJSON file
    regions = gpd.read_file(region_geojson_path)

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
    min_bin = data_choropleth_sums['DENSITE'][data_choropleth_sums['DENSITE'] > 0].min()
    min_bin = max(min_bin, 1e-10)
    max_bin = data_choropleth_sums['DENSITE'].max() * 1.01
    num_bins = 6
    bins = np.logspace(np.log10(min_bin), np.log10(max_bin), num_bins)

    # Initialize the map centered on France
    map_center = [46.2276, 2.2137]  # Coordinates for France
    m = folium.Map(location=map_center, zoom_start=6)

    # Create the choropleth map
    folium.Choropleth(
        geo_data=regions.to_json(),
        name='Densité de Déchets',
        data=data_choropleth_sums,
        columns=['LIEU_REGION', 'DENSITE'],
        key_on='feature.properties.nom',
        fill_color='Reds',
        bins=bins,
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Densité de Déchets'
    ).add_to(m)

    return m



def make_density_choropleth(data_choropleth_sums, region_geojson_path):
    # Load all regions from the GeoJSON file
    regions_geojson = requests.get(region_geojson_path).json()

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
        #color_continuous_midpoint=np.median(data_choropleth_sums['DENSITE']),
        #range_color=(min_density, max_density),
        labels={'DENSITE': 'Densité de Déchets'}
    )

    # Update layout to fit the map to the boundaries of the GeoJSON
    choropleth.update_layout(
        geo=dict(
            fitbounds="locations",
            visible=False
        ),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    # Disable axis ticks and labels and set country borders to red
    choropleth.update_geos(
        resolution=50,
        showcountries=True, countrycolor="red"
    )

    # Disable the display of other countries' borders
    choropleth.update_geos(
        showcountries=False,
        showcoastlines=False,
        showland=False,
        showocean=False
    )

    return choropleth



#######################
# Dashboard Main Panel#
#######################

col = st.columns((1.5, 4.5, 2), gap='medium')

# Construct the map
with col[1]:
    st.markdown('### Spots Adoptés')
    m = plot_adopted_waste_spots(data_zds, filter_dict, REGION_GEOJSON_PATH)
    # Show the adopted spots map on the streamlit tab
    if m:
        folium_static(m)

    st.markdown('### Densité des déchets')
    choropleth = make_density_choropleth(data_choropleth_sums, REGION_GEOJSON_PATH)
    st.plotly_chart(choropleth, use_container_width=True)


    st.markdown('### Densité des déchets')
    m = plot_waste_density_choropleth(data_zds, REGION_GEOJSON_PATH)
    if m:
        folium_static(m)

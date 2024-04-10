import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster

from utils import construct_query_string

def plot_adopted_waste_spots(data_zds: pd.DataFrame,
                             filter_dict: dict,
                             region_geojson_path: str,
                             ) -> folium.Map:
    """Show a folium innteractive map of adopted spots within a selected region,
    filtered by environments of deposit.
    Arguments:
    - data_zds: The waste dataframe
    - filter_dict: dictionary mapping the name of the column in the waste df and the value you want to filter by
    """
    ####################################
    # 1/ Create the waste geodataframe #
    ####################################

    # Create a GeoDataFrame for waste points
    gdf = gpd.GeoDataFrame(
        data_zds,
        geometry = gpd.points_from_xy(data_zds["LIEU_COORD_GPS_X"], data_zds["LIEU_COORD_GPS_Y"]),
        crs = "EPSG:4326"
    )

    # Construct the query string
    query_string = construct_query_string(**filter_dict)

    # Filter the geodataframe by region and by environment
    gdf_filtered = gdf.query(query_string)

    ######################################
    # 2/ Create the regions geodataframe #
    ######################################

    # Unpack the region name
    region = filter_dict["REGION"]

    # Load France regions from a GeoJSON file
    regions = gpd.read_file(region_geojson_path)
    regions = regions.loc[regions["nom"] == region, :]

    # Filter the region geodataframe for the specified region
    selected_region = regions[regions["nom"].str.lower() == region.lower()]
    if selected_region.empty:
        raise KeyError(f"Region '{region}' not found.")

    ############################
    # 3/ Initialize folium map #
    ############################

    # Initialize a folium map, centered around the mean location of the waste points
    map_center = [gdf_filtered.geometry.y.mean(), gdf_filtered.geometry.x.mean()]
    m = folium.Map(location = map_center, zoom_start = 5)  # Adjust zoom_start as needed for the best initial view

    ######################
    # 4/ Add the markers #
    ######################

    # Use MarkerCluster to manage markers if dealing with a large number of points
    marker_cluster = MarkerCluster().add_to(m)

    # Add each waste point as a marker on the folium map
    for _, row in gdf_filtered.iterrows():
        # Define the marker color: green for adopted spots, red for others
        marker_color = 'darkgreen' if row['SPOT_A1S'] else 'red'
        # Define the icon: check-circle for adopted, info-sign for others
        icon_type = 'check-circle' if row['SPOT_A1S'] else 'info-sign'

        folium.Marker(
            location = [row.geometry.y, row.geometry.x],
            popup = f"Zone: {row['NOM_ZONE']}<br>Date: {row['DATE']}<br>Volume: {row['VOLUME_TOTAL']} litres",
            icon = folium.Icon(color = marker_color, icon = icon_type, prefix = 'fa')
        ).add_to(marker_cluster)

    ##############################
    # 5/ Add the region boundary #
    ##############################

    # Add the region boundary to the map for context
    folium.GeoJson(
        selected_region,
        name = "Region Boundary",
        style_function = lambda feature: {
            'weight': 2,
            'fillOpacity': 0.1,
        }
    ).add_to(m)

    # Return the map
    return m

import streamlit as st
import altair as alt
import pandas as pd
import duckdb

from hotspots_functions.maps import plot_adopted_waste_spots
from hotspots_functions.params import (
    NB_DECHETS_PATH,
    DATA_ZDS_PATH,
    REGION_GEOJSON_PATH,
)


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

# Create 2 columns for 2 filters
columns = st.columns(2)

# Choice of the region
x1 = data_zds["REGION"].unique()
f1 = columns[0].selectbox("Seléctionnez une région (par défaut votre région) :", x1)
columns[0].write(f1)

# Choice of the environment
x2 = data_zds["TYPE_MILIEU"].unique()
f2 = columns[0].selectbox("Seléctionnez un environnement :", x2)
columns[0].write(f2)

# Create the filter dict
filter_dict = {"REGION": f1, "TYPE_MILIEU": f2}

# Create the map of the adopted spots
plot_adopted_waste_spots(data_zds, filter_dict, region_geojson_path=REGION_GEOJSON_PATH)

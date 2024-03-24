import dash
from dash import html, dcc, callback, Input, Output
import plotly.express as px
import pandas as pd
import duckdb

dash.register_page(__name__)

df_nb_dechet = pd.read_csv(
    (
        "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
        "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
        "sation/data/data_releve_nb_dechet.csv"
    )
)

df_other = pd.read_csv(
    (
        "https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-"
        "nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visuali"
        "sation/data/data_zds_enriched.csv"
    )
)

res_aggCategory_filGroup = duckdb.query(
    (
        "SELECT categorie, sum(nb_dechet) AS total_dechet "
        "FROM df_nb_dechet "
        "WHERE type_regroupement = 'GROUPE' "
        "GROUP BY categorie "
        "HAVING sum(nb_dechet) > 10000 "
        "ORDER BY total_dechet ASC;"
    )
).to_df()

fig = px.bar(
    res_aggCategory_filGroup,
    x="total_dechet",
    y="categorie",
    orientation="h",
    height=1000,
)

layout = html.Div([html.H1("HOTSPOTS"), dcc.Graph(id="template", figure=fig)])

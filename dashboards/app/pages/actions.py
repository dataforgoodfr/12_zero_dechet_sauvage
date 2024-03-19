import dash
from dash import html, dcc, callback, Input, Output
import plotly.express as px
import pandas as pd

dash.register_page(__name__)

df = pd.read_excel("https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visualisation/data/data_zds_enriched.xlsx",
	sheet_name="Sheet1"
)

fig = px.scatter(df, x='DATE', y='VERSION_PROTOCOLE')

layout = html.Div([
    html.H1('This is our Analytics page'),
    dcc.Graph(id='random-graph', figure=fig)
])

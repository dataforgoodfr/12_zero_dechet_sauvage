import dash
from dash import html, dash_table
import pandas as pd

dash.register_page(__name__, path='/')

df = pd.read_excel("https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visualisation/data/data_zds_enriched.xlsx",
	sheet_name="Sheet1"
)

df_tbl =  df[["DATE", "NOM_EVENEMENT", "NOM_STRUCTURE", "NB_PARTICIPANTS", "VERSION_PROTOCOLE"]]

layout = html.Div([
    html.H1('Test de tableau 👇'),
    dash_table.DataTable(df_tbl.to_dict("records"), [{"name": i, "id": i} for i in df_tbl.columns], id='tbl')
])

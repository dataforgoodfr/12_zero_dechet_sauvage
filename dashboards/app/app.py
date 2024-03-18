from dash import Dash, html, dcc, callback, Output, Input, dash_table
import plotly.express as px
import pandas as pd

# df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

df = pd.read_excel("https://github.com/dataforgoodfr/12_zero_dechet_sauvage/raw/2-nettoyage-et-augmentation-des-donn%C3%A9es/Exploration_visualisation/data/data_zds_enriched.xlsx",
	sheet_name="Sheet1"
)

df_tbl =  df[["ID_RELEVE", "NOM_EVENEMENT", "NOM_STRUCTURE", "NB_PARTICIPANTS"]]

app = Dash(__name__)

app.layout = html.Div([
    html.H1(children='ZeroDechetSauvage', style={'textAlign':'center'}),
	dash_table.DataTable(df_tbl.to_dict("records"), [{"name": i, "id": i} for i in df_tbl.columns], id='tbl')
#    dcc.Dropdown(df.country.unique(), 'Canada', id='dropdown-selection'),
#    dcc.Graph(id='graph-content')
])

# @callback(
#     Output('graph-content', 'figure'),
#     Input('dropdown-selection', 'value')
# )
# def update_graph(value):
#     dff = df[df.country==value]
#     return px.line(dff, x='year', y='pop')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="8050", debug=True)

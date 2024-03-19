import dash
from dash import Dash, html, dcc#, callback, Output, Input 
import plotly.express as px

app = Dash(__name__, use_pages=True)

app.layout = html.Div([
    html.H1(children='ZeroDechetSauvage', style={'textAlign':'center'}),
    html.Div([
        html.Div(
            dcc.Link(f"Onglet {str(page['name']).upper()}", href=page["relative_path"])
        ) for page in dash.page_registry.values()
    ]),
    dash.page_container,
])

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="8050", debug=True)

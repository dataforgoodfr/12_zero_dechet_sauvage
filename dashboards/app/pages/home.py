import dash
from dash import html, dash_table

dash.register_page(__name__, path="/")

layout = html.Div(
    [
        html.H1("Oh, hello there 👋")
    ]
)

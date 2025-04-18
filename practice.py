import dash
from dash import Dash, html, dcc, Output
import plotly.express as px
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import sqlite3 as db


class DataBase:
    def __init__(self, maxlen=1000):
        self.connection = db.connect("databaseFile.db",check_same_thread=False )
        self.cur = self.connection.cursor()

    def getLastRow(self):

        return pd.read_sql_query("SELECT * FROM storeHouse ORDER BY time_stamp DESC LIMIT 1", con=self.connection)
    def getAllData(self):
        return pd.read_sql_query("SELECT * FROM storeHouse ORDER BY time_stamp DESC", con=self.connection)
    def close(self):
        self.connection.commit()
        self.connection.close()

store = DataBase()

app = Dash(__name__)


def getSpeedGraph():
    df = store.getAllData()
    speedFig = go.Figure(
        data=[
            go.Scatter(
                x=df['time_stamp'],
                y=df['speed'],
                mode='lines',
            )
        ],
        layout=go.Layout(
            title='Motor Speed (steps/sec)',
            yaxis={"range": [0,800]},
        )
    )
    return speedFig

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.H3(children="Dashboard", className="lContent"),
                html.Div(children=[
                    html.Button(children="Download Data", n_clicks=0, className="successBtn"),
                ])
            ], className="navbar"
        ),
        html.Div(
            children=[
                html.Div([
                    dcc.Dropdown(["Speed", "Area", "Objects", "Show All"],value=["Show All"],multi=True, className="dropDownContainer", id="graph_selector"),

                    dcc.DatePickerRange(id="date_ranger"),

                    html.Button('Get Data', n_clicks=0, className="grayBtn", id="get_graphs_btn"),
                ], className="graphBar"),

                html.Div([
                    html.P(["Graph"], className="lContent"),
                    dcc.Graph(figure={}, id="objects_graph")
                ])
            ]
        )
    ]
)

@app.callback(
    Output('objects-graph', 'figure'),
    Input('date_ranger', 'value'),
)

def update_graph(nClicks, graphs):
    pass

if __name__ == "__main__":
    app.run(debug=True)
import dash
from dash import Dash, html, dcc, Output, Input, State, ctx
import plotly.express as px
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import sqlite3 as db
import datetime

class DataBase:
    def __init__(self):
        self.connection = db.connect("databaseFile.db",check_same_thread=False )
        self.cur = self.connection.cursor()

    def getLastRow(self):
        return pd.read_sql_query("SELECT * FROM storeHouse ORDER BY time_stamp DESC LIMIT ?", con=self.connection, params=[1])
    def getAllData(self):
        return pd.read_sql_query("SELECT * FROM storeHouse ORDER BY time_stamp DESC", con=self.connection)
    def close(self):
        self.connection.commit()
        self.connection.close()
    def getSelectedData(self, startDate, endDate):
        start_date = self._parse_date(startDate) or datetime.date.today()
        end_date = self._parse_date(endDate) or datetime.date.today()

        # Format dates for SQL query
        start_str = start_date.strftime('%Y-%m-%d 00:00:00')
        end_str = end_date.strftime('%Y-%m-%d 23:59:59')

        query = """
                    SELECT * 
                    FROM storeHouse 
                    WHERE time_stamp >= ? AND time_stamp <= ?
                """
        return pd.read_sql_query(query, con=self.connection, params=[start_str, end_str])

    def groupByData(self, grpBy):
        group_expr = {
            'Day': "DATE(time_stamp)",
            'Month': "STRFTIME('%Y-%m', time_stamp)",
            'Week': "STRFTIME('%Y-W%W', time_stamp)",
            'Year': "STRFTIME('%Y', time_stamp)",
            'Hour': "STRFTIME('%Y-%m-%d %H:00', time_stamp)",
            'Minute': "STRFTIME('%Y-%m-%d %H:%M', time_stamp)"
        }.get(grpBy)

        if not group_expr:
            raise ValueError("Invalid grouping period")

        query = f"""
            SELECT
                *,
                {group_expr} as time_period,
                AVG(speed) as avgSpeed,
                COUNT(*) as record_count
            FROM storeHouse
            GROUP BY time_period
            ORDER BY time_period
            """
        return pd.read_sql_query(query, self.connection)

    def _parse_date(self, date_str):
        """Helper method to parse date strings into date objects."""
        if not date_str:
            return None
        try:
            return datetime.datetime.strptime(str(date_str), "%Y-%m-%d").date()
        except ValueError:
            return None

store = DataBase()

data = store.getAllData()
print(store.groupByData("Minute"))

app = Dash(__name__)

def getAllGraphs(graphsSelector,df, deltaXLabel):
    fig = go.Figure()

    for graph_name in graphsSelector:
        if graph_name.lower() == "area":
            fig.add_trace(
                go.Scatter(
                    x=df['time_stamp'] if not deltaXLabel else df['time_period'],
                    y=df[graph_name.lower()],
                    name=graph_name,
                    mode='lines+markers',
                    fill="tozeroy",
                    fillcolor='rgba(255, 0, 0, 0.1)'
                )
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=df['time_stamp'] if not deltaXLabel else df['time_period'],
                    y=df[graph_name.lower()],
                    name=graph_name,
                    mode='lines+markers',
                )
            )
    def getTitle():
        return ",".join(graphsSelector)

    fig.update_layout(
        title=f'{getTitle()} Graphs',
        xaxis_title="time_period",
        hovermode="x unified"
    )
    return fig

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.H3(children="Dashboard", className="lContent"),
                html.Div(children=[
                    dcc.Dropdown(options=["csv", "sql db", "Excel"], value="csv", id="file_format", className="fileDropDown"),
                    html.Button(children="Download Full Data", n_clicks=0, className="successBtn", id="download_data_btn"),
                    dcc.Download(id="download_data_frame")
                ], className="navbarBtnsGrp"),

            ], className="navbar"
        ),
        dcc.Interval(id='update_interval', interval=1000, n_intervals=0),
        html.Div([
                    html.P(["Live Graph"], className="lContent"),
                    dcc.Graph(id='live_graph_container',
                              config={'displayModeBar': True},
                              style={'height': '400px'})
                ], className="graphsContainer"),
        html.Div(
            children=[
                html.Div([
                    dcc.Dropdown(["Speed", "Area", "Objects"],value=["Speed"],multi=True, className="dropDownContainer", id="graph_selector"),

                    dcc.DatePickerRange(id="date_ranger"),
                    dcc.Dropdown(['Day','Month','Week','Year','Hour','Minute'], id="group_by_selector"),
                    html.Button('Get Data', n_clicks=0, className="grayBtn", id="get_graphs_btn"),

                ], className="graphBar"),

                html.Div([
                    dcc.Graph(id='graph_container',
                              config={'displayModeBar': True},
                              style={'height': '400px'})
                ])
            ], className="graphsContainer")
    ]
)



@app.callback(
    Output("live_graph_container", "figure"),
    Input('update_interval', 'n_intervals')
)
def update_live_graph(n_intervals):
    startDate = endDate = None
    df = store.getSelectedData(startDate, endDate)
    graphsOptions = ['Speed', 'Area', 'Objects']
    fig = getAllGraphs(graphsOptions, df, False)
    return fig

@app.callback(
    Output('graph_container', 'figure'),
    Input('get_graphs_btn', 'n_clicks'),
    State('graph_selector', 'value'),
    State('date_ranger', 'start_date'),
    State('date_ranger', 'end_date'),
    State('group_by_selector', 'value'),
)

def update_graph(click, graphsSelector, startDate, endDate, grpBy):
    df = store.getSelectedData(startDate, endDate)
    deltaXLabel = False
    if grpBy:
        df = store.groupByData(grpBy)
    fig = getAllGraphs(graphsSelector, df, deltaXLabel)
    return fig

@app.callback(
Output('download_data_frame', 'data'),
    Input('download_data_btn', 'n_clicks'),
    State("file_format", 'value'),
    prevent_initial_call=True
)


def download_data(downloadClick,formatOption):
    currDate = datetime.date.today()
    df = store.getAllData()
    if formatOption == 'csv':
        return dcc.send_data_frame(df.to_csv, f"data_downloaded_{currDate}.csv")
    elif formatOption == 'Excel':
        return dcc.send_data_frame(df.to_excel, f"data_downloaded_{currDate}.xlsx", sheet_name="Sheet_name_1")

if __name__ == "__main__":
    app.run(debug=True)
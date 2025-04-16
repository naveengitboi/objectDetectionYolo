import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import pandas as pd
import threading
import time
import queue
import mainCode2 as mc
import sqlite3 as db

# Initialize app
app = dash.Dash(__name__, title='Conveyor Monitoring Dashboard')

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

# Layout
app.layout = html.Div([
    html.H1("Conveyor Motor Dashboard 5", style={'textAlign': 'center'}),
    dcc.Store(id='memory-store'),
    dcc.Interval(id='update-interval', interval=1000, n_intervals=0),
    html.Div([
        html.Div([
            dcc.Graph(id='speed-graph',
                      config={'displayModeBar': False},
                      style={'height': '400px'})
        ], className='six columns'),
        html.Div([
            dcc.Graph(id='objects-graph',
                      config={'displayModeBar': False},
                      style={'height': '400px'})
        ], className='six columns'),
    ], className='row'),
    html.Div([
        html.Div([
            dcc.Graph(id='area-graph',
                      config={'displayModeBar': False},
                      style={'height': '400px'})
        ], className='six columns'),
        html.Div([
            html.Div(id='current-status',
                     style={'fontSize': '24px', 'padding': '20px'}),
            html.Div([
                dcc.Markdown("**Live Data Feed:**"),
                html.Div(id='live-feed',
                         style={'whiteSpace': 'pre-line',
                                'fontFamily': 'monospace'})
            ], style={'padding': '20px'})
        ], className='six columns'),
    ], className='row')
])


# Callbacks
@app.callback(
    [Output('speed-graph', 'figure'),
     Output('objects-graph', 'figure'),
     Output('area-graph', 'figure'),
     Output('current-status', 'children'),
     Output('live-feed', 'children')],
    [Input('update-interval', 'n_intervals')]
)



def update_graphs(n):
    df = pd.DataFrame(store.getAllData())
    print(type(df))
    print(df)
    if len(df) == 0:
        empty_fig = go.Figure(layout=go.Layout(title='Waiting for data...'))
        return empty_fig, empty_fig, empty_fig, "No data received", "Waiting for first data point..."

    # Speed Graph
    speed_fig = go.Figure(
        data=[go.Scatter(
            x=df['time_stamp'],
            y=df['speed'],
            mode='lines+markers',
            line={'color': '#1f77b4'},
            name='Speed'
        )],
        layout=go.Layout(
            title='Motor Speed (steps/sec)',
            yaxis={'range': [0, 900]}
        )
    )

    # Objects Graph
    objects_fig = go.Figure(
        data=[go.Bar(
            x=df['time_stamp'],
            y=df['objects'],
            marker_color='#ff7f0e',
            name='Objects'
        )],
        layout=go.Layout(
            title='Object Count',
            yaxis={'range': [0, max(df['objects'].max() + 5, 10)]}
        )
    )

    # Area Graph
    area_fig = go.Figure(
        data=[go.Scatter(
            x=df['time_stamp'],
            y=df['area'],
            fill='tozeroy',
            mode='lines',
            line={'color': '#2ca02c'},
            name='Area'
        )],
        layout=go.Layout(
            title='Total Area (cm²)',
            yaxis={'range': [0, max(df['area'].max() + 100, 500)]}
        )
    )

    # Status text
    latest = df.iloc[-1]
    status = f"Current: Speed={latest['speed']} | Objects={latest['objects']} | Area={latest['area']}cm²"

    # Live feed text
    live_feed = "\n".join(
        f"Speed={row['speed']}, "
        f"Objects={row['objects']}, "
        f"Area={row['area']}"
        for _, row in df.tail(5).iterrows()
    )

    return speed_fig, objects_fig, area_fig, status, live_feed


# Data collection thread
def data_collection_thread():
    while True:
        try:
            if not mc.data_store.queue.empty():
                print("Inside If Block")
                speed, objects, area = mc.data_store.queue.get_nowait()
                mc.data_store.add_data(speed, objects, area)
                print(f"Received data: {speed}, {objects}, {area}")  # Debug
        except queue.Empty:
            time.sleep(0.1)
        except Exception as e:
            print(f"Error in data collection: {e}")
            time.sleep(1)


if __name__ == '__main__':
    # # Start data thread
    # thread = threading.Thread(target=data_collection_thread, daemon=True)
    # thread.start()

    # Run app
    app.run(debug=True, port=8050)
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import pandas as pd
import storeHouse
import sqlite3 as db
import storeHouse
import time
# Initialize Dash app


app = dash.Dash(__name__, title='Conveyor Monitoring Dashboard')
app.layout = html.Div([
    html.H1("Conveyor Motor Dashboard", style={'textAlign': 'center'}),
    dcc.Interval(id='update-interval', interval=1000, n_intervals=0),
    html.Div([
        html.Div(dcc.Graph(id='speed-graph'), className='six columns'),
        html.Div(dcc.Graph(id='objects-graph'), className='six columns'),
    ], className='row'),
    html.Div([
        html.Div(dcc.Graph(id='area-graph'), className='six columns'),
        html.Div([
            html.Div(id='current-status', style={'fontSize': '24px'}),
            html.Pre(id='debug-console', style={
                'backgroundColor': 'black',
                'color': 'white',
                'padding': '10px',
                'height': '200px',
                'overflowY': 'scroll'
            })
        ], className='six columns'),
    ], className='row')
])


@app.callback(
    [Output('speed-graph', 'figure'),
     Output('objects-graph', 'figure'),
     Output('area-graph', 'figure'),
     Output('current-status', 'children')],
    [Input('update-interval', 'n_intervals')]
)
def update_dashboard(n):
    df = storeHouse.getFullData()
    print("Data frame", df)
    data = pd.DataFrame(df)
    print("DataFrame pd ", data)

    if len(df) == 0:
        empty_fig = go.Figure(layout={'title': 'Waiting for data...'})
        return empty_fig, empty_fig, empty_fig, "No data received"


    # Create figures
    speed_fig = go.Figure(
        data=[go.Scatter(
            x=df['timestamp'],
            y=df['speed'],
            mode='lines+markers',
            line={'color': '#1f77b4'}
        )],
        layout=go.Layout(
            title='Motor Speed (steps/sec)',
            yaxis={'range': [0, max(df['speed'].max() + 50, 800)]}
        )
    )

    objects_fig = go.Figure(
        data=[go.Bar(
            x=df['timestamp'],
            y=df['objects'],
        )],
        layout=go.Layout(
            title='Object Count',
            yaxis={'range': [0, max(df['objects'].max() + 2, 10)]}
        )
    )

    area_fig = go.Figure(
        data=[go.Scatter(
            x=df['timestamp'],
            y=df['area'],
            fill='tozeroy',
            line={'color': '#2ca02c'}
        )],
        layout=go.Layout(
            title='Total Area (cm²)',
            yaxis={'range': [0, max(df['area'].max() + 100, 2000)]}
        )
    )

    status = f"Current: Speed={df['speed'].iloc[-1]} | Objects={df['objects'].iloc[-1]} | Area={df['area'].iloc[-1]}cm²"

    return speed_fig, objects_fig, area_fig, status


# def data_collection_thread():
#     while True:
#         try:
#             # Get with timeout to prevent CPU spin
#             speed, objects, area = data_store.queue[-1]
#             data_store.add_data(speed, objects, area)
#             print(f"📊 Data stored | Speed: {speed} | Objects: {objects} | Area: {area}")
#         except not queue.Full:
#             print("Queue is empty yet")
#             continue
#         except Exception as e:
#             print(f"Data collection error: {e}")
#             time.sleep(1)

if __name__ == '__main__':
    # Start data collection thread
    # threading.Thread(target=data_collection_thread, daemon=True).start()

    # Run dashboard
    print("🌐 Dashboard running at http://localhost:8050")
    app.run(debug=False, port=8050)
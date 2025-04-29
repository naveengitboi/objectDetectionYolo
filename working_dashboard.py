import dash
from dash import Dash, html, dcc, Output, Input, State, ctx
import plotly.express as px
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import datetime
from shared_data import DataStore


store = DataStore(make_table=False)
data = store.get_all_data()
print(store.group_by_data("Minute"))

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
                    dcc.Dropdown(options=["csv", "Excel"], value="csv", id="file_format", className="fileDropDown"),
                    html.Button(children="Download Full Data", n_clicks=0, className="successBtn", id="download_data_btn"),
                    dcc.Download(id="download_data_frame")
                ], className="navbarBtnsGrp"),

            ], className="navbar"
        ),
        html.Div([
                html.Div([
                    # html.P(["Last Added Load"], className="lContent"),
                    html.P('Last Added Load, Category One(gms)', className='miniContent'),
                    html.H1('250', className="weightValue", id="load_status"),
                ], className="load"),
                html.Div([
                    html.P('Motor One(steps/s)', className='miniContent'),
                    html.H1('250', className="weightValue", id="motor_1_speed"),
                ], className="load"),
                html.Div([
                    html.P('Motor Two(steps/s)', className='miniContent'),
                    html.H1('250', className="weightValue", id="motor_2_speed"),
                ], className="load")
                ], className="loadContainer"),
        dcc.Interval(id='update_interval', interval=1000, n_intervals=0),
        html.Div([
                html.P(["Live Graph Of Seg_Belt"], className="lContent"),
                dcc.Graph(id='live_graph_seg_container',
                              config={'displayModeBar': True},
                              style={'height': '400px'}),
                html.P(["Live Graph Of Pickup_Belt"], className="lContent"),
                dcc.Graph(id='live_graph_pickup_container',
                          config={'displayModeBar': True},
                      style={'height': '400px'}),
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
    Output("live_graph_seg_container", "figure"),
        Output("live_graph_pickup_container", "figure"),
        Output("load_status", 'children'),
        Output("motor_1_speed", 'children'),
        Output("motor_2_speed", 'children'),
    Input('update_interval', 'n_intervals')
)
def update_live_graph(n_intervals):
    startDate = endDate = None
    seg_belt_df = store.get_selected_data(startDate, endDate, 'seg_belt')
    pickup_belt_df = store.get_selected_data(startDate, endDate, 'pickup_belt')
    print("updated",n_intervals)
    seg_belt_graph_options = ['Speed', 'Area', 'Objects']
    pickup_belt_graph_options = ['Speed', 'Area', 'Objects']
    seg_fig = getAllGraphs(seg_belt_graph_options, seg_belt_df, False)
    pickup_fig = getAllGraphs(pickup_belt_graph_options, pickup_belt_df, False )
    last_load = store.get_last_load()
    last_speed_motor_one = store.get_last_row('seg_belt')['speed']
    last_speed_motor_two = store.get_last_row('pickup_belt')['speed']
    print("last load",last_speed_motor_one, last_speed_motor_two)
    last_load_value = 250
    if(last_load.size != 0):
        last_load_value = last_load['weight']
    return seg_fig, pickup_fig, last_load_value, last_speed_motor_one, last_speed_motor_two

@app.callback(
    Output('graph_container', 'figure'),
    Input('get_graphs_btn', 'n_clicks'),
    State('graph_selector', 'value'),
    State('date_ranger', 'start_date'),
    State('date_ranger', 'end_date'),
    State('group_by_selector', 'value'),
)

def update_graph(click, graphsSelector, startDate, endDate, grpBy):
    df = store.get_selected_data(startDate, endDate)
    deltaXLabel = False
    if grpBy:
        df = store.group_by_data(grpBy)
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
    df = store.get_all_data()
    if formatOption == 'csv':
        return dcc.send_data_frame(df.to_csv, f"data_downloaded_{currDate}.csv")
    elif formatOption == 'Excel':
        return dcc.send_data_frame(df.to_excel, f"data_downloaded_{currDate}.xlsx", sheet_name="Sheet_name_1")

if __name__ == "__main__":
    app.run(debug=True)
import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import plotly.express as px
from collections import deque
import pandas as pd
import subprocess
from PIL import Image
from analytics.Analytics import ObluAnalytics


FILE_PATH = 'data/BatteryTemperature.csv'
file = open(FILE_PATH, 'r')
WINDOW_SIZE = 25
Y = deque(maxlen=200)  # plotting each battery temperature as y value
INTERVAL = 1000  # Timer for updating the graph in milli seconds

df = pd.read_csv(FILE_PATH, header=None)
# Variable for storing Departure Score from Analytics
S = deque(maxlen=WINDOW_SIZE)
S.append(1)  # 1 is random value to begin plotting.

# Variable for Time step
T = deque(maxlen=WINDOW_SIZE)
T.append(1)

# Object for analytics
obj = ObluAnalytics(lag_vector_length=WINDOW_SIZE)
UT, centroid, theta = obj.get_threshold_score(FILE_PATH)

# Initialize app

app = dash.Dash(
            __name__,
            meta_tags=[
                {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
            ],
        )

#  Starting Layout
app.layout = html.Div(
    id="root",
    children=[
        html.Div(
            id="header",
            children=[
                html.Img(id="logo", src=app.get_asset_url("logo.png")),
                # html.Pre(id="logo", children='BlueTrack Security'),
                html.H4(children="Satellite telemetry tracker"),
                html.P(
                    id="description",
                    children="Detecting a potential stealthy Cyber attack in satellite telemetry data",
                ),
            ],
        ),

        html.Div(
            id="app-container",
            children=[
                html.Div(
                    id="left-column",  # left-column
                    children=[
                        dcc.Graph(id='live-telemetry', animate=True),
                        dcc.Interval(id='telemetry-update', interval=INTERVAL, n_intervals=0),
                    ],
                ),
                html.Div(
                    id="graph-container",  # right-column
                    children=[
                        dcc.Graph(id='app-analytics', animate=True),
                        dcc.Interval(id='analytics-update', interval=INTERVAL, n_intervals=0),
                        # html.P(id="chart-selector", children="Select chart:"),

                    ],
                ),
            ],
        ),

        html.Div(
            id='footer',
            children=[
                html.Pre('Credits'),
                html.Pre('Karan Basson'),
                html.Pre('Indian Institute of Technology Kanpur - 2018'),
                html.Pre('Source Code: link'),
            ]
        )
    ],
)
#  End of Layout


#  Starting Callback functions

@app.callback(Output('app-analytics', 'figure'),
              [Input('analytics-update', 'n_intervals')])
def update_analytics(n):
    global S, obj, UT, centroid, theta, WINDOW_SIZE
    global Y
    # S.append(S[-1]+(random.uniform(-.5,.5)))
    T.append(T[-1] + 1)
    # print([pd.DataFrame(x) for x in zip(list(X),list(Y))])
    # print(pd.DataFrame([sum(x)/2 for x in zip(list(X), list(Y))]))
    # print('UT={}, centroid={}, theta={}'.format(UT, centroid, theta))
    if len(T) >= WINDOW_SIZE:
        # stream = [sum(x)/2 for x in list(zip(list(X),list(Y)))]
        # df = pd.DataFrame(list(X))
        # df = df[0] / 2
        score = obj.get_score(UT, centroid, None, Y)
        # print(score)
        S.append(score)

    realtime_data = go.Scatter(
        x=list(T),
        y=list(S),
        name='Realtime Anomaly Score',
        mode='lines',
        # showlegend=False,
    )
    threshold_data = go.Scatter(
        x=[min(T), max(T) + 20],
        y=[float(theta)] * 50,
        name='Threshold Score',
        mode='lines',
        # showlegend=False,
    )
    layout = go.Layout(
        # title='Analytics-Live',
        xaxis=dict(range=[min(T), max(T) + 20]),
        # yaxis=dict(range=[min(S),max(S)]),
        yaxis=dict(range=[0, 100]),
        template='plotly_dark',
        uirevision='analytics-update',

    )

    fig = go.Figure(data=[realtime_data, threshold_data],
                    layout=layout)
    fig.update_layout(xaxis_title="No of Steps",
                      yaxis_title="Score", )
    legend = dict(
        x=0,
        y=1,
        traceorder="normal",
        font=dict(
            family="sans-serif",
            size=12,
            color="black"
        ),
        bgcolor="LightSteelBlue",
        bordercolor="Black",
        borderwidth=2
    )
    fig.update_layout(legend=legend)
    return fig


# @app.callback(Output('app-plotid', 'style'),
#               [Input('rotate-slider', 'value')])
# def update_style(value):
#     return {'transform': 'rotate({}deg)'.format(value)}


# @app.callback(
#     dash.dependencies.Output('map', 'hidden'),
#     [dash.dependencies.Input('map_checkbox', 'value')])
# def update_output(value):
#     if value:
#         return False
#     else:
#         return True


@app.callback(
    Output('live-telemetry', 'figure'),
    [Input('telemetry-update', 'n_intervals')]
)
def update_telemetry(n):
    global Y
    # Y.append(df[1][n])
    line = file.readline()
    value = line.split(',')[-1]
    Y.append(value)
    telemetry_data = go.Scatter(
        y=list(Y),
        name='Scatter',
        mode='lines+markers'
    )

    layout = go.Layout(
        xaxis=dict(range=[0, len(Y)+30]),  # Time axis
        yaxis=dict(range=[-10, 25]),
        height=500,
        showlegend=False,
        uirevision='telemetry-update'
    )

    # Create figure
    fig = go.Figure(
        data=[telemetry_data],
        layout=layout
    )
    fig.update_layout(xaxis_title="Time Steps",
                      yaxis_title="Battery Temperature", )
    # Fine tune layout
    fig.update_layout(template="plotly_dark")
    # fig.update_xaxes(showticklabels=False, zeroline=False)
    # fig.update_yaxes(showticklabels=False, zeroline=False)
    fig.update_layout(xaxis_showgrid=False, yaxis_showgrid=False)
    fig.update_layout(dragmode='pan')
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)

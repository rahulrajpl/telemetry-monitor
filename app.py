import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from collections import deque
import subprocess
from PIL import Image
from analytics.Analytics import ObluAnalytics


# For reading the last line of sensor data values stored in a file
def tail():
    result = subprocess.run(['tail', '-1', 'data/steps.txt'], stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')


# For offline steps plotting
# file = open('sensor/GetData/steps.txt', 'r')
file = open('analytics/steps_test.txt', 'r')
# ignoring the first line
file.readline()

img = Image.open('assets/rm3_1.png')

max_trail_limit = 15
X = deque(maxlen=max_trail_limit)
Y = deque(maxlen=max_trail_limit)
interval = 5000  # Timer for updating the graph in milli seconds

# Initial data
initial_data = tail()
print(initial_data)
X.append(initial_data.split(',')[1])
Y.append(initial_data.split(',')[2])

# external_stylesheets = [
#     'https://codepen.io/chriddyp/pen/bWLwgP.css',
#     {
#         'href': 'https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css',
#         'rel': 'stylesheet',
#         'integrity': 'sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO',
#         'crossorigin': 'anonymous'
#     }
# ]

# Variable for storing Departure Score from Analytics
S = deque(maxlen=max_trail_limit)
S.append(5)  # 5 is random value to begin plotting.

# Variable for Time step
T = deque(maxlen=max_trail_limit)
T.append(1)

# Object for analytics
obj = ObluAnalytics(lag_vector_length=max_trail_limit)
UT, centroid, theta = obj.get_threshold_score('analytics/steps_train.txt')

# Initialize app

app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)
server = app.server

app.layout = html.Div(
    id="root",
    children=[
        html.Div(
            id="header",
            children=[
                html.Img(id="logo", src=app.get_asset_url("logo.png")),
                # html.Pre(id="logo", children='BlueTrack Security'),
                html.H4(children="Pedestrian Dead Reckoning and Anomaly Detector"),
                html.P(
                    id="description",
                    children="Application for mapping and detecting anomalies in the PDR data from Oblu sensor",
                ),
            ],
        ),

        html.Div(
            id="app-container",
            children=[
                html.Div(
                    id="left-column",
                    children=[
                        html.Div(
                            className="app-image",
                            id="heatmap-container",

                            children=[
                                html.P(
                                    "Track received from sensor",
                                    id="heatmap-titles",
                                ),
                                html.Img(id='map', src=img, alt='bg_image', hidden=False,)
                            ]
                        ),
                        html.Div(
                            id="app-plotid",
                            children=[
                                dcc.Graph(
                                    id='live-graph',
                                    animate=False,
                                    config={
                                        'autosizable': True,
                                        'scrollZoom': True,
                                        'displayModeBar': False,
                                    }
                                ),
                            ],
                        ),
                        html.Div(
                            id="slider-container",
                            children=[
                                html.P(
                                    id="slider-text",
                                    children="Drag the slider to change the plot orientation:",
                                ),
                                dcc.Slider(
                                    id='rotate-slider',
                                    min=-180,
                                    max=180,
                                    step=2,
                                    value=0
                                ),
                                html.Div(id='slider-output-container'),
                                dcc.Interval(
                                    id='graph-update',
                                    interval=interval,
                                    n_intervals=0
                                ),
                                html.Br(),
                                dcc.Checklist(
                                    id='map_checkbox',
                                    options=[
                                        {'label': 'Show background Map', 'value': 'show_map'}
                                    ],
                                ),
                                html.Br(),
                                # html.P(
                                #     children="Drag the slider to change the opacity of plot:",
                                # ),
                                # dcc.Slider(
                                #     id='map_opacity_slider',
                                #     min=-5,
                                #     max=10,
                                #     step=0.5,
                                #     value=-3
                                # ),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    id="graph-container",  # right-column
                    children=[
                        dcc.Graph(id='app-analytics', animate=True),
                        dcc.Interval(id='analytics-update', interval=interval, n_intervals=0),
                        # html.P(id="chart-selector", children="Select chart:"),

                    ],
                ),
            ],
        ),

        html.Div(
            id='footer',
            children=[
                html.Pre('Credits'),
                html.Pre('Rahul Raj'),
                html.Pre('Indian Institute of Technology Kanpur - 2018'),
                html.Pre('Source Code: link'),
            ]
        )
    ],
)


@app.callback(Output('app-analytics', 'figure'),
              [Input('analytics-update', 'n_intervals')])
def update_analytics(n):
    global S, obj, UT, centroid, theta, max_trail_limit
    global X
    global Y
    # S.append(S[-1]+(random.uniform(-.5,.5)))
    T.append(T[-1] + 1)
    # print([pd.DataFrame(x) for x in zip(list(X),list(Y))])
    # print(pd.DataFrame([sum(x)/2 for x in zip(list(X), list(Y))]))
    # print('UT={}, centroid={}, theta={}'.format(UT, centroid, theta))
    if len(T) >= max_trail_limit:
        # stream = [sum(x)/2 for x in list(zip(list(X),list(Y)))]
        # df = pd.DataFrame(list(X))
        # df = df[0] / 2
        score = obj.get_score(UT, centroid, X, Y)
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


@app.callback(Output('app-plotid', 'style'),
              [Input('rotate-slider', 'value')])
def update_style(value):
    return {'transform': 'rotate({}deg)'.format(value)}


@app.callback(
    dash.dependencies.Output('map', 'hidden'),
    [dash.dependencies.Input('map_checkbox', 'value')])
def update_output(value):
    if value:
        return False
    else:
        return True


@app.callback(
    Output('live-graph', 'figure'),
    [Input('graph-update', 'n_intervals')]
)
def update_graph(n):
    global X
    global Y
    # global counter
    # counter += interval/1000
    # -----------------------------------------------------
    # For real-time plot
    # new_x = str(tail()).split(',')[1]
    # new_y = str(tail()).split(',')[2]
    # -----------------------------------------------------

    # -----------------------------------------------------
    # For simulating data saved in real-time
    if not file == "":
        file_data = file.readline().split(',')
        print(file_data)
        new_x, new_y = file_data[1], file_data[2]
    else:
        file.seek(0, 0)
    # # print(new_x, new_y)
    # -----------------------------------------------------

    if not (X == new_x and Y == new_y):
        X.append(new_x)
        Y.append(new_y)

    # # Add trace
    plot_data = go.Scatter(
        x=list(X),
        y=list(Y),
        name='Scatter',
        mode='lines+markers'
        # mode = 'lines'
    )

    x_range = [-20, 65]
    y_range = [-30, 65]

    layout = go.Layout(xaxis=dict(range=x_range),
                       yaxis=dict(range=y_range),
                       height=500,
                       showlegend=False,
                       uirevision='graph-update',
                       paper_bgcolor='rgba(0,0,0,0)',
                       plot_bgcolor='rgba(0,0,0,0)',
                       )

    # Create figure
    fig = go.Figure(
        data=[plot_data],
        layout=layout
    )

    # Fine tune layout
    # fig.update_layout(template="plotly_white")
    fig.update_xaxes(showticklabels=False, zeroline=False)
    fig.update_yaxes(showticklabels=False, zeroline=False)
    fig.update_layout(xaxis_showgrid=False, yaxis_showgrid=False)
    fig.update_layout(dragmode='pan')
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)

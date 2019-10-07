import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
import datetime as dt
import base64
import os
import plotly.graph_objs as go
import json
import psycopg2
import pandas.io.sql as sqlio
import matplotlib

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# dependencies
dbname='videodetect_db01'
user='videodetect01'
password='VideoDetect01!'
host='34.244.229.213'
port=8060
good_photos_folder_name = 'photos'
schedule_json_name = 'schedule.json'

# connect to DB and read a DataFrame from DB
conn = psycopg2.connect(dbname=dbname, 
                        user=user, 
                        password=password, 
                        host=host)
cursor = conn.cursor()
sql = "select * from users_aggregate;"
df = sqlio.read_sql_query(sql, conn)
conn = None

# create a list of matplotlib colors
hex_colors_dic = {}
rgb_colors_dic = {}
hex_colors_only = []
for name, hex in matplotlib.colors.cnames.items():
    hex_colors_only.append(hex)
    hex_colors_dic[name] = hex
    rgb_colors_dic[name] = matplotlib.colors.to_rgb(hex)

# colors that look ok on the dashboard
norm_colors = ['lightslategrey',                
               'mediumaquamarine', 
               'lightseagreen', 
               'mediumpurple', 
               'cornflowerblue', 
               'lightpink',
               'steelblue', 
               'palevioletred',
               'lightskyblue', 
               'rgb(216, 191, 216)',
               'rgb(108, 79, 126)',
               'rgb(3, 156, 148)', 
               'darkseagreen', 
               'lightcoral',
               'mediumvioletred']

with open(schedule_json_name, 'r') as f:
    schedule_dict = json.load(f)

# append colors from hex_colors_only if there ate not enough colors in norm_colors
for i in range(len(schedule_dict)-len(norm_colors)):
    norm_colors.append(hex_colors_only[i])

# create dictionary where each person is associated with a color
color_dict = dict(zip(schedule_dict.keys(), norm_colors))

# construct DataFrame's final look
df['Month'] = df.time_start.dt.strftime('%B')
df['Day'] = df.time_start.dt.day

body = dbc.Container([dbc.Row(html.Div([
                                html.P(children='Month statistics', 
                                       style = {'marginBottom': '7%', 
                                                'marginLeft': '95%', 
                                                'textAlign': 'center', 
                                                'font-size': '40px', 
                                                'width': '100%',
                                                'font-family': "Courier New, monospace", 
                                                'color': "#2B1232", 
                                                'font-style': 'bold'})]),
                            ),
                      dbc.Row([dbc.Col(html.Div(
                                        html.P(children = 'Month: ',  
                                               style = {'textAlign': 'center', 
                                                        'marginTop': '1%',
                                                        'marginBottom': '7%',
                                                        'font-size': '20px',
                                                        'font-family': "Courier New, monospace", 
                                                        'color': "#595B68"}))),
                               dbc.Col(dcc.Dropdown(
                                        id = 'month',
                                        options=[{'label': month, 'value': month}
                                        for month in df['Month'].unique()],
                                        value=dt.datetime.now().strftime('%B'), 
                                        style = {'textAlign': 'left', 
                                                 'marginLeft': '-20%', 
                                                 'marginTop': '1%', 
                                                 'font-size': '20px',
                                                 'font-family': "Courier New, monospace", 
                                                 'color': "#595B68",
                                                 'width': '95%'
                                                }
                                    )),
                               
                               html.Div([dcc.Interval(id='interval-component',
                                             interval=1*1000, # in milliseconds
                                             n_intervals=0)])
                              ]),
                      dbc.Row(html.Div(dcc.Graph(id = 'work-attendance', 
                                                 style = {'width': '100%',
                                                          'height': '75vh',
                                                          'marginBottom': '0%'}), style = {'width': '100%', 'height': '100%'}))
                     ],style = {'height': '97vh', 'width': '100vw'})

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([body], style={'backgroundImage': 'url(\'https://img3.akspic.ru/image/28815-angle-kvadrat-uzor-geometriya-simmetriya-1920x1080.jpg\')'})

@app.callback(dash.dependencies.Output('work-attendance', 'figure'),
             [dash.dependencies.Input('interval-component', 'n_intervals'),
              dash.dependencies.Input('month', 'value')])

def update_num_of_hours(n_intervals, month):
    
    conn = psycopg2.connect(dbname=dbname, 
                            user=user, 
                            password=password, 
                            host=host)
    cursor = conn.cursor()
    sql = "select * from users_aggregate;"
    df = sqlio.read_sql_query(sql, conn)
    conn = None

    df['Month'] = df.time_start.dt.strftime('%B')
    df['Day'] = df.time_start.dt.day
    
    data = []
    
    df_month = df[(df['Month'] == month)]
    
    df_plot = pd.DataFrame()
    df_plot['person_id'] = list(color_dict.keys())
    df_plot = df_plot.merge(df_month, how='outer', on='person_id')
    
    df_plot.sort_values(by=['Day'], inplace=True)
    
    for pers in df_plot.person_id.unique():
        df_pers = df_plot[df_plot.person_id==pers]
        data.append({'x': df_pers['Day'].values,
                         'y': df_pers.person_id,
                         'mode': 'markers',
                         'marker':{'size': 9,
                                   'color': color_dict[pers],
                                   'opacity': 0.9},
                         'name': pers, 'text':pers,
                    'hoverinfo':'text'})
    return {
            'data': data,
            'layout': {'hovermode':'x',
                'hoverinfo':'text',
                       'title': 'Attendance of office in '+month,
                       'plot_bgcolor': 'rgba(255, 255, 255, 0)',
                       'paper_bgcolor': 'rgba(255, 255, 255, 0.4)',
                       'font': {'color': '#595B68'},
                       'yaxis': {'automargin': True},
                       'xaxis': {'dtick':1, 
                                 'type': 'category',
                                 'autorange': False}
                      }
            }

if __name__ == "__main__":
    app.run_server(debug = False, port=port)

import base64
import io
import os
import time
from datetime import datetime
from threading import Thread

import socket
import email.utils as eut
from geolite2 import geolite2
from newspaper import Article

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

import pandas as pd
import plotly.graph_objs as go

from google.cloud import vision
from google.cloud.vision import types

from image_processing import *

app = dash.Dash()

app.layout = html.Div(children=[

    html.H1(children="Web Image Analytics Tool"),

    html.Div(id="main-container",
             children=[
                html.H3('Image'),
                html.Div(id="image-container",
                         children=[
                            dcc.Upload(id='upload-data',
                                        children=html.Div(['Drag and Drop or ',
                                                           html.A('Select Files')]),
                                        style={'width': '80%',
                                               'height': '30px',
                                               'lineHeight': '30px',
                                               'borderWidth': '1px',
                                               'borderStyle': 'dashed',
                                               'borderRadius': '5px',
                                               'textAlign': 'center',
                                               'margin': '8%'},
                                        multiple=False),
                            html.Div(id="output-image",
                                      style={'marginLeft': "15%",
                                             'marginRight': "15%",
                                             "padding": "auto"}), ]),
                            html.Div(id="hover-data"),
                html.H3('Controls'),
                html.Div(id="controls-container",
                         children=[
                             html.P(children="Rotation"),
                             dcc.Slider(id='rotation-slider',
                                        min=-90,
                                        max=90,
                                        step=0.5,
                                        marks={i: '{}'.format(
                                            i) for i in range(-90, 91, 45)},
                                        value=0,),
                             html.P(children="X Crop"),
                             dcc.RangeSlider(id='x-crop-slider',
                                             min=0,
                                             max=100,
                                             step=0.1,
                                             marks={i: '{}'.format(
                                                 i) for i in range(0, 101, 10)},
                                             value=[0, 100]),
                             html.P(children="Y Crop"),
                             dcc.RangeSlider(id='y-crop-slider',
                                             min=0,
                                             max=100,
                                             step=0.1,
                                             marks={i: ''.format(
                                                 i) for i in range(0, 101, 10)},
                                             value=[0, 100]),
                         ], style={'marginLeft': "5%",
                                   'marginRight': "5%",
                                   'marginTop': "1%"}),

             ], style={'columnCount': 4}),

    dcc.Graph(id='timeline-graph'),

    # hidden fields
    html.Div(id="working-image", style={"display": "none"}),
    html.Div(id="working-annotations", style={"display": "none"}),

], style={'marginLeft': "5%",
          'marginRight': "5%",
          'marginTop': "1%"})


def get_image_meta(img_url, result_dict, key):
    try:
        img_url = str(img_url).split("?")[0]
        conn = urllib.request.urlopen(img_url, timeout=3)
        date_time = str(conn.headers['last-modified'])
        ip_a = socket.gethostbyname(urlparse(img_url).netloc)
        reader = geolite2.reader()
        country = reader.get(ip_a)['country']['names']['en']
        result_dict[key].append(
            {"image_url": img_url, "image_time": date_time, "country": country})

    except Exception as e:
        print(e)


@app.callback(
    Output(component_id='working-annotations', component_property='children'),
    [Input(component_id='rotation-slider', component_property='value'),
     Input(component_id='x-crop-slider', component_property='value'),
     Input(component_id='y-crop-slider', component_property='value'),
     Input(component_id='working-image', component_property='children')]
)
def update_output_img(rotation_value, xcrop, ycrop, working_image):
    print("Updating output image")
    image_raw = base64_decode_image(working_image)
    image = imread(image_raw)
    image = rotate_image(image, int(rotation_value))

    # cropping
    im_x, im_y = image.shape[1], image.shape[0]
    xstart, xend = int(xcrop[0])/100, int(xcrop[1])/100
    ystart, yend = int(ycrop[0])/100, int(ycrop[1])/100
    image = image[int(im_y*ystart):int(im_y*yend),
                  int(im_x*xstart):int(im_x*xend)]

    # convert back to RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Cloud Vision API
    scratch_file = "/tmp/"+str(time.time())+".jpg"
    cv2.imwrite(scratch_file, image)
    with io.open(scratch_file, 'rb') as image_file:
        content = image_file.read()
    client = vision.ImageAnnotatorClient()
    image = vision.types.Image(content=content)
    response = client.web_detection(image=image, max_results=1000)
    annotations = response.web_detection

    appearances = {}
    appearances["full_matches"] = []
    appearances["partial_matches"] = []
    appearances["visually_similar"] = []

    threads = []

    for page in annotations.pages_with_matching_images:
        for image in page.full_matching_images:
            try:
                img_url = image.url
                result_dict = appearances
                key = "full_matches"
                t = Thread(target=get_image_meta, args=(
                    img_url, result_dict, key))
                threads.append(t)
                t.start()
            except Exception as e:
                print(e)
                pass

        for image in page.partial_matching_images:
            try:
                img_url = image.url
                result_dict = appearances
                key = "partial_matches"
                t = Thread(target=get_image_meta, args=(
                    img_url, result_dict, key))
                threads.append(t)
                t.start()
            except Exception as e:
                print(e)
                pass

    [t.join() for t in threads]

    return str(json.dumps(appearances))


@app.callback(Output(component_id='timeline-graph', component_property='figure'),
              [Input(component_id='working-annotations', component_property='children')])
def update_timeline_graph(appearances):
    appearances = json.loads(appearances)

    graph_a = []

    appearances_full_match = []
    appearances_full_match_time = []
    appearances_full_match_url = []

    appearances_partial_match = []
    appearances_partial_match_time = []
    appearances_partial_match_url = []

    for image in appearances["full_matches"]:
        try:
            appearances_full_match.append(1.2)
            date = image["image_time"]
            date_eut = eut.parsedate(date)
            date = str(date_eut[0])+"-"+str(date_eut[1])+"-"+str(date_eut[3])
            print(date)  # 2016-07-01
            appearances_full_match_time.append(date)
            appearances_full_match_url.append(image["image_url"])
        except Exception as e:
            print(e)

    for image in appearances["partial_matches"]:
        try:
            appearances_partial_match.append(0.8)
            date = image["image_time"]
            date_eut = eut.parsedate(date)
            date = str(date_eut[0])+"-"+str(date_eut[1])+"-"+str(date_eut[3])
            print(date)
            appearances_partial_match_time.append(date)
            appearances_partial_match_url.append(image["image_url"])
        except Exception as e:
            print(e)

    graph_a.append(go.Scatter(
        x=appearances_full_match_time,
        y=appearances_full_match,
        text=appearances_full_match_url,
        mode='markers',
        opacity=0.5,
        marker={
            'size': 15,
        },
        name="Full Matches"
    ))

    graph_a.append(go.Scatter(
        x=appearances_partial_match_time,
        y=appearances_partial_match,
        text=appearances_partial_match_url,
        mode='markers',
        opacity=0.5,
        marker={
            'size': 15,
        },
        name="Partial Matches"
    ))

    return {
        'data': graph_a,
        'layout': go.Layout(
            xaxis={'type': 'date'},
            yaxis={'title': 'Appearances', 'range': [0.5, 1.5]},
            legend={'x': 0, 'y': 1},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            hovermode='closest'
        )
    }


@app.callback(
    Output('hover-data', 'children'),
    [Input('timeline-graph', 'hoverData')])
def display_hover_data(hoverData):
    data = hoverData
    if float(data["points"][0]["y"]) < 1:
        type_ = "Partial Match: "
    else:
        type_ = "Full Match: "
    img_src = str(data["points"][0]["text"])
    ret = [html.Img(src=img_src, style={'height': '200px', "marginLeft": "10%", "marginRight": "10%"}),
           html.P(type_+img_src)]
    return ret


@app.callback(Output('working-image', 'children'),
              [Input('upload-data', 'contents'),
               Input('upload-data', 'filename'),
               Input('upload-data', 'last_modified')])
def update_working(image, filename, last_modified):
    print("Updating working image")
    image = image.replace("data:image/jpeg;base64,", "")
    image = image.replace("data:image/png;base64,", "")
    return image


@app.callback(
    Output(component_id='output-image', component_property='children'),
    [Input(component_id='rotation-slider', component_property='value'),
     Input(component_id='x-crop-slider', component_property='value'),
     Input(component_id='y-crop-slider', component_property='value'),
     Input(component_id='working-image', component_property='children')]
)
def update_output_img(rotation_value, xcrop, ycrop, working_image):
    print("Updating output image")
    image_raw = base64_decode_image(working_image)
    image = imread(image_raw)
    image = rotate_image(image, int(rotation_value))

    # cropping
    im_x, im_y = image.shape[1], image.shape[0]
    xstart, xend = int(xcrop[0])/100, int(xcrop[1])/100
    ystart, yend = int(ycrop[0])/100, int(ycrop[1])/100
    image = image[int(im_y*ystart):int(im_y*yend),
                  int(im_x*xstart):int(im_x*xend)]

    # convert back to RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    ret, buffer = cv2.imencode('.jpg', image)
    buffer = base64.b64encode(buffer)

    buffer = 'data:image/jpeg;base64,{}'.format(buffer.decode("utf8"))
    return html.Img(src=buffer, style={'height': '200px', "marginLeft": "10%", "marginRight": "10%"})


if __name__ == '__main__':
    app.run_server(debug=True)

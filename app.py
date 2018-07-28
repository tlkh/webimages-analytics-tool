import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import base64

from image_processing import *

app = dash.Dash()

app.layout = html.Div(children=[
    html.H1(children="Web Image Analytics Tool"),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=False
    ),

    html.Div(id='output-image'),

    dcc.Slider(
        id='rotation-slider',
        min=-90,
        max=90,
        step=1,
        value=0,
    ),

    html.Div(id='working-image', style={'display': 'none'})

])


@app.callback(Output('working-image', 'children'),
              [Input('upload-data', 'contents'),
               Input('upload-data', 'filename'),
               Input('upload-data', 'last_modified')])
def update_working(image, filename, last_modified):
    return image


@app.callback(
    Output(component_id='output-image', component_property='children'),
    [Input(component_id='rotation-slider', component_property='value'),
     Input(component_id='working-image', component_property='children')]
)
def update_output_img(rotation_value, working_image):
    image_raw = base64_decode_image(working_image)
    image = imread(image_raw)
    image = rotate_image(image, int(rotation_value))
    return html.Img(src=image)


if __name__ == '__main__':
    app.run_server(debug=True)

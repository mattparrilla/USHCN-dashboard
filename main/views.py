from main import app
from flask import render_template, send_file, make_response
from webargs import Arg
from webargs.flaskparser import use_args
from csv_to_png import make_image
from cStringIO import StringIO
from main import ABSOLUTE_PATH
import json


@app.route('/')
def index():
    title = "USHCN Data Mapping"
    description = "Taking USHCN data and trying to tell a story with it"

    with open('%s/static/colorbrewer.json' % ABSOLUTE_PATH, 'rU') as f:
        colorbrewer = json.load(f)
        palettes = sorted(colorbrewer.keys())

    return render_template('content.html',
        title=title,
        description=description,
        palettes=palettes)


image_args = {
    'filename': Arg(str, default='btv'),
    'fill_null': Arg(bool, default=True),
    'smooth_horizontal': Arg(bool, use=lambda n: n == 'on'),
    'smooth_vertical': Arg(bool, use=lambda n: n == 'on'),
    'palette': Arg(str, default='Set1'),
    'bins': Arg(str, default='8'),
    'data_width': Arg(int, default=2),
    'data_height': Arg(int, default=4),
    'continuity': Arg(float, default=0.2),
    'recursion': Arg(int, default=3),
    'start_index': Arg(int, default=0),
    'save_image': Arg(bool),
}


@app.route('/img/')
@use_args(image_args)
def get_image(args):

    image, name = make_image(**args)
    img_io = StringIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)

    if args['save_image']:
        response = make_response(img_io.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=%s" % name
        return response
    else:
        return send_file(img_io, mimetype='image/png')

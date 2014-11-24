from flask import Flask, render_template, request, send_file
from webargs import Arg
from webargs.flaskparser import use_args
from csv_to_png import make_image
from cStringIO import StringIO
import json

from pprint import pprint

app = Flask(__name__)


@app.route('/')
def index():
    title = "USHCN Data Mapping"
    description = "Taking USHCN data and trying to tell a story with it"

    with open('colorbrewer.json', 'rU') as f:
        colorbrewer = json.load(f)
        palettes = sorted(colorbrewer.keys())

    return render_template('content.html',
        title=title,
        description=description,
        palettes=palettes)


def serve_pil_image(pil_img):
    img_io = StringIO()
    pil_img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


image_args = {
    'f_n': Arg(str, default='btv'),
    'fill_null': Arg(bool, default=True),
    'unit': Arg(str, default='day'),
    'smooth_horizontal': Arg(bool, default=True),
    'smooth_vertical': Arg(bool, default=True),
    'palette': Arg(str, default='Set1'),
    'bins': Arg(str, default='8'),
    'x_d': Arg(int, default=2),
    'y_d': Arg(int, default=4),
    'continuity': Arg(float, default=0.2),
    'recursion': Arg(int, default=3),
    'start_idx': Arg(bool, default=False),
    'save_image': Arg(bool, default=False),
}

@app.route('/img/')
@use_args(image_args)
def get_image(args):

    image, name = make_image(args)
    pprint(args)
    print name
    return serve_pil_image(image)

if __name__ == '__main__':
    app.run(debug=True)

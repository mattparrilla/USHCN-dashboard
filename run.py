from flask import Flask, render_template, request, send_file
from csv_to_png import make_image
from cStringIO import StringIO
import json

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


@app.route('/img/')
def get_image():
    image, name = make_image(**request.args.to_dict())
    print request.args
    print name
    return serve_pil_image(image)

if __name__ == '__main__':
    app.run(debug=True)

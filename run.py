from flask import Flask, render_template, request, send_file
from csv_to_png import make_image
from cStringIO import StringIO

app = Flask(__name__)


@app.route('/')
def index():
    title = "USHCN Data Mapping"
    description = "Taking USHCN data and trying to tell a story with it"

    return render_template('content.html',
        title=title,
        description=description)


def serve_pil_image(pil_img):
    img_io = StringIO()
    pil_img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


@app.route('/img/')
def get_image():
    print request.args
    image = make_image(**request.args)
    return serve_pil_image(image)

if __name__ == '__main__':
    app.run(debug=True)

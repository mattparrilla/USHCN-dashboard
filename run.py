from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    title = "USHCN Data Mapping"
    description = "Taking USHCN data and trying to tell a story with it"
    return render_template('content.html',
        title=title,
        description=description)

if __name__ == '__main__':
    app.run(debug=True)

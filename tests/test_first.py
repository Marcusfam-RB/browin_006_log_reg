from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return "<H1>Hello, Flask!<H2>"


@app.route('/')
def second():
    return render_template('second.html', phone="88005553535")


if __name__ == '__main__':
    app.run(debug=True)

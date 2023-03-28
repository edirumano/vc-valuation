from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST',])
def submit():
    value = float(request.form['value'])
    shares = float(request.form['shares'])
    result = value * shares
    return render_template('response.html', form=request.form, result=result)
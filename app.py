from flask import Flask, render_template, request
from bot.py import TODO#function to define

app = Flask(__name__)

# set up our landing page
@app.route('/')
def index():
	return render_template('index.html')

# only use this when posting data!
@app.route('/', methods=['POST'])
def index_post():
	user_question = request.form['req_question']
	return render_template('index.html')

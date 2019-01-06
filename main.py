from flask import Flask
from MrLing import ling_blueprint
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'random string'
app.debug = True
app.register_blueprint(ling_blueprint)

@app.route("/")
def home():
    return '<a href="/MrLing">ling</a>'

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = int(os.getenv('PORT', 5000)))
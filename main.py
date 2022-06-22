from flask import Flask

import numpy as np
import pandas as pd


# create and configure the app
app = Flask(__name__)


@app.route('/search/<string:query>')
def search(query):
    return 'Search'

@app.route('/search_nutrition/<string:nutrient>')
def search_nutrition(nutrient):
    return 'Search Nutrition'
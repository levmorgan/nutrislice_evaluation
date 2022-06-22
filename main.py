import os
from flask import Flask, g, jsonify

import pandas as pd


app = Flask(__name__)


# Data loading methods
def load_data():
    err_str = ("Couldn't find or read {}, make sure the app is being run " +
               "from the Nutraslice Interview directory.")

    if not os.path.exists("./data"):
        raise FileNotFoundError(err_str.format("./data/"))

    data_paths = [("food_data", "./data/food_data.csv"),
                  ("menu_data", "./data/menu_data.csv"),
                  ("nutrition_data", "./data/nutrition_data.csv")]

    data = {}

    for key, infi in data_paths:
        try:
            df = pd.read_csv(infi, delimiter="\t", header=0)
            data[key] = df
        except (FileNotFoundError, PermissionError):
            raise FileNotFoundError(err_str.format(infi))

    data = process_data(data)

    return data


def process_data(data):
    food_data, menu_data, nutrition_data = (data['food_data'],
                                            data['menu_data'],
                                            data['nutrition_data'])

    # Disambiguate column names
    menu_data.columns = ["menu_id", "menu_name"]
    food_data.columns = ['food_name', 'food_id',
                         'description', 'price', 'image_ref', 'import_name']
    nutrition_data.columns = ['nutrition_id',
                              'food_id', 'vitamin_d', 'vitamin_c', 'calcium']

    # Add nutrition data to food data, dropping nutrition_id
    food_data = food_data.merge(nutrition_data.iloc[:, 1:],
                                left_on="food_id", right_on="food_id",
                                how="outer")

    return {"food_data": food_data, "menu_data": menu_data,
            "nutrition_data": nutrition_data}


# Helper methods for APIs
def filter_foods(query, mode="namedesc"):
    # TODO: This should be a more general method that can match any field.
    data = get_data()
    food_data = data["food_data"]
    _query = query.strip().lower()

    if mode == "namedesc":
        results = food_data[
            food_data['food_name'].str.contains(_query, case=False) |
            food_data['description'].str.contains(_query, case=False)
        ]
    elif mode == "nutrient":
        results = food_data[
            ~food_data[_query].isna()
        ]

    # Calculate based on 10 results per page, even though we return 5
    pages_left = int((len(results)-1)/10.)

    # Format results object for endpoint
    results = results[["food_id", "food_name", "price"]]
    results["menu_count"] = 0
    results = results.sort_values(by="food_name")
    results = results.iloc[:min(len(results), 5), :]
    results = results.set_index("food_id")
    results = {"results": results.values.tolist(), "pages_left": pages_left}

    return results


def get_data():
    if 'data' not in g:
        g.data = load_data()

    return g.data


# API Endpoints
@app.route('/search/<string:query>', methods=["GET"])
def search(query):
    results = filter_foods(query, "namedesc")

    return jsonify(results)


@app.route('/search_nutrients/<string:nutrient>', methods=["GET"])
def search_nutrition(nutrient):
    results = filter_foods(nutrient, "nutrient")

    return jsonify(results)


if __name__ == "__main__":
    with app.app_context():
        try:
            get_data()
        except FileNotFoundError as e:
            app.logger.error(e)
            raise
    app.run()

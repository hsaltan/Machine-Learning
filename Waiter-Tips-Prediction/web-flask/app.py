"""
    This module has the app script.

    This script requires that `flask` be installed within the Python environment you are
    running this script in. `predict` module created with this script also needs to be
    loaded.

    User enters the features set as input on the web application, and the script then
    computes the tip amount using the `predict` function, which loads and uses the best
    xgboost model obtained in the training phase.

    This file contains the following functions:

        * my_form - displays the web page, text and dropdown boxes
        * enter - receives user input on the web page and computes the prediction
"""

# Import libraries
import sys

sys.path.insert(1, "/home/ubuntu/app/Waiter-Tips-Prediction/dags/app")
from flask import Flask, render_template, request
from predict import predict

app = Flask(__name__)


@app.route("/")
def my_form():

    """
    Displays the web page, text and dropdown boxes
    """

    smokers = ["Non-smoker", "Smoker"]
    genders = ["Female", "Male"]
    week_days = ["Thursday", "Friday", "Saturday", "Sunday"]
    day_times = ["Lunch", "Dinner"]

    return render_template(
        "index.html",
        smokers=smokers,
        genders=genders,
        week_days=week_days,
        day_times=day_times,
    )


@app.route("/", methods=["POST", "GET"])
def enter():

    """
    Receives user input on the web page and computes the prediction.
    """

    if request.method == "POST":
        total_bill = request.form["nm"]
        size = request.form["rm"]
        smoker_value = request.form.get("smoker")
        gender_value = request.form.get("gender")
        week_day_value = request.form.get("week_day")
        day_time_value = request.form.get("day_time")
        results = {}
        results["total_bill"] = float(total_bill)
        results["smoker"] = smoker_value
        results["gender"] = gender_value
        results["week_day"] = week_day_value
        results["time"] = day_time_value
        results["number_of_people"] = int(size)
        prediction = predict(results)

        return render_template(
            "index.html",
            result=prediction,
            total_bill=total_bill,
            size=size,
            smoker_value=smoker_value,
            gender_value=gender_value,
            week_day_value=week_day_value,
            day_time_value=day_time_value,
        )

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3500)

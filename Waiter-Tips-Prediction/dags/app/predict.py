"""
    This is the app that predicts the waiter tip and returns the result.

    This script requires that `numpy` and `mlflow` be installed within the Python
    environment you are running this script in. `aws_utils` is a util module created
    with this script, which also needs be loaded.

    The script loads the best model, takes features as an input, hot-encodes them and
    puts them into the model to predict.

    This file can also be imported as a module and contains the following
    functions:

        * load_model - loads the ML model
        * transform_data - takes feature input and hot-encodes it
        * predict - returns the prediction
"""

# Import libraries
import sys

sys.path.insert(
    1, "/home/ubuntu/Waiter-Tips-Prediction/dags/utils"
)
from typing import Any, Union

import aws_utils as aws
import mlflow
import numpy as np


def load_model() -> Any:

    """
    Loads the best model from the local folder or cloud bucket.
    """

    logged_model = aws.get_parameter("logged_model")
    loaded_model = mlflow.pyfunc.load_model(logged_model)

    return loaded_model


def transform_data(input_dict: dict[str, Union[int, float]]) -> list[Union[int, float]]:

    """
    Hot-encodes the data provided.
    """

    # Hot-encoding values
    gender = {"Female": 0, "Male": 1}
    smoker = {"Non-smoker": 0, "Smoker": 1}
    week_day = {"Thursday": 0, "Friday": 1, "Saturday": 2, "Sunday": 3}
    day_time = {"Lunch": 0, "Dinner": 1}

    # Replace the source dictionary values with the hot-encoding values
    input_dict["smoker"] = smoker[input_dict["smoker"]]
    input_dict["gender"] = gender[input_dict["gender"]]
    input_dict["week_day"] = week_day[input_dict["week_day"]]
    input_dict["time"] = day_time[input_dict["time"]]

    # Create features input to the model
    total_bill = input_dict["total_bill"]
    sex = input_dict["gender"]
    smoker = input_dict["smoker"]
    day = input_dict["week_day"]
    day_time = input_dict["time"]
    size = input_dict["number_of_people"]

    features = np.array([[total_bill, sex, smoker, day, day_time, size]])

    return features


def predict(input_dict: dict[str, Union[int, float]]) -> float:

    """
    Using the best model and features entered by user,
    predicts the target value.
    """

    # Load the model
    model = load_model()

    # Transform data
    features = transform_data(input_dict)

    # Make the prediction
    prediction = model.predict(features)[0]

    return f"{prediction:.2f}"

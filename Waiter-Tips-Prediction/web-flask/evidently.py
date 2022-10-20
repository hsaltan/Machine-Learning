"""
    This module puts all reports produced by evidently together on the web application.

    This script requires that `flask` be installed within the Python environment you are
    running this script in.

    This file contains the following functions:

        * data_drift_report - returns data_drift_dashboard as html
        * data_quality_report - returns data_quality_dashboard as html
        * target_drift_report - returns data_target_drift_dashboard as html
        * regression_model_perform_report - returns regression_model_performance_dashboard
        as html
"""

# Import libraries
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def data_drift_report():

    """
    Returns data_drift_dashboard as html
    """

    return render_template("data_drift_dashboard.html")


@app.route("/data-quality")
def data_quality_report():

    """
    Returns data_quality_dashboard as html
    """

    return render_template("data_quality_dashboard.html")


@app.route("/target-drift")
def target_drift_report():

    """
    Returns data_target_drift_dashboard as html
    """

    return render_template("data_target_drift_dashboard.html")


@app.route("/regression-performance")
def regression_model_perform_report():

    """
    Returns regression_model_performance_dashboard as html
    """

    return render_template("regression_model_performance_dashboard.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3600)

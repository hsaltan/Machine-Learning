"""
    This module computes and displays monitoring data and metrics, checks if any
    drift occurs, and notifies the user.

    This script requires that `pandas`, `prometheus_client`, and `evidently`, `numpy`,
    and `mlflow` be installed within the Python environment you are running this script in.
    `aws_utils` and `airflow_utils` are util modules created with this script, which
    also needs be loaded.

    The script prepares the dataset until ready to be fed into monitoring tools, splits the
    data as 'reference' and 'current' to compare and see if any data drift occurs when the
    new data comes in, creates and saves the monitoring dashboards, notifies the user of the
    results by email, also records metrics in MLFlow, and visualizes the metrics on Grafana.

    This file can also be imported as a module and contains the following
    functions:

        * rename_columns - renames the columns in a dataframe, and changes the data type of columns
        * prepare_evidently_data - loads and transforms feature datasets to create evidently
        reports and metrics.
        * create_evidently_reports - creates and saves evidently dashboards as html
        * send_email - sends data drift results via AWS SNS
        * evaluate_data_drift - evaluates data drifts
        * record_metrics - records data drift evaluation results in MLFlow
        * monitor_evidently - initiates evidently monitoring, and computes the data metrics
"""

# Import libraries
import json
import logging
from typing import Any, Dict, List, Literal, Union

import pandas as pd
import prometheus_client as pc
from evidently.dashboard import Dashboard
from evidently.dashboard.tabs import (
    DataDriftTab,
    DataQualityTab,
    NumTargetDriftTab,
    RegressionPerformanceTab,
)
from evidently.model_monitoring import (
    DataDriftMonitor,
    DataQualityMonitor,
    ModelMonitoring,
    NumTargetDriftMonitor,
    RegressionPerformanceMonitor,
)
from evidently.model_profile import Profile
from evidently.model_profile.sections import DataDriftProfileSection
from evidently.pipeline.column_mapping import ColumnMapping
from utils.airflow_utils import get_vars
from utils.aws_utils import get_parameter, put_object, send_sns_topic_message

# Define the column mapping
column_mapping = ColumnMapping()
column_mapping.target = (
    "target"  # 'target' is the name of the column with the target function
)
column_mapping.prediction = (
    "prediction"  # 'prediction' is the name of the column(s) with model predictions
)
column_mapping.id = None  # There is no ID column in the dataset

column_mapping.numerical_features = ["total_bill", "size"]  # List of numerical features
column_mapping.categorical_features = [
    "sex",
    "smoker",
    "day",
    "time",
]  # List of categorical features


def rename_columns(
    data_frame: pd.DataFrame, old_names: list[str], new_names: list[str]
) -> pd.DataFrame:

    """
    Renames the columns in a dataframe, and changes the data type of columns.
    """

    # Rename the columns
    cols_dict = dict(zip(old_names, new_names))
    data_frame.rename(columns=cols_dict, inplace=True)

    # Change type of the feature columns
    if len(new_names) > 1:
        convert_dict = {x: int for x in new_names[1:]}
        data_frame = data_frame.astype(convert_dict)

    logging.info("Columns are renamed as defined in '%s'.", cols_dict)

    return data_frame


def prepare_evidently_data() -> pd.DataFrame:

    """
    Orchestrates the loading, transformation and preparation of the training and
    validation feature datasets for creating evidently reports and metrics.
    """

    import mlflow
    import numpy as np

    # Retrieve variables
    bucket, _, local_path, _, _, _, _ = get_vars()

    # Load the model
    logged_model = get_parameter("logged_model")
    loaded_model = mlflow.pyfunc.load_model(logged_model)

    def get_prediction(data_frame: pd.DataFrame) -> Any:

        """
        Turns the dataframe into a numpy array, and computes
        the predicted value with the model based on input features.
        """

        shape = data_frame.shape[0]  # 6
        arr = data_frame.to_numpy()
        arr = np.reshape(arr, (-1, shape))
        prediction = loaded_model.predict(arr)[0]
        logging.info(
            "Predictions are computed for and added to the given feature dataframes."
        )

        return prediction

    # Load processed datasets from the local storage
    x_train = pd.read_csv(f"{local_path}data/X_train.csv")
    x_val = pd.read_csv(f"{local_path}data/X_val.csv")
    y_train = pd.read_csv(f"{local_path}data/y_train.csv")
    y_val = pd.read_csv(f"{local_path}data/y_val.csv")
    logging.info(
        "Dataset is retrieved from the local storage path '%sdata' as pandas dataframe.",
        local_path,
    )

    # Rename the target columns of the label datasets as 'target'
    y_train_target = y_train.columns.to_list()[0]
    y_train = rename_columns(y_train, [y_train_target], ["target"])

    y_val_target = y_val.columns.to_list()[0]
    y_val = rename_columns(y_val, [y_val_target], ["target"])

    # Rename the columns of the feature datasets
    columns = ["total_bill", "sex", "smoker", "day", "time", "size"]
    x_train_cols = x_train.columns.to_list()
    x_val_cols = x_val.columns.to_list()

    x_train = rename_columns(x_train, x_train_cols, columns)
    x_val = rename_columns(x_val, x_val_cols, columns)

    # Add 'target' column to feature datasets
    x_train["target"] = y_train["target"]
    x_val["target"] = y_val["target"]
    logging.info(
        "Actual labels are added to the given feature dataframes as 'target' column."
    )

    # Add 'prediction' column to feature datasets
    x_train["prediction"] = x_train[columns].apply(get_prediction, axis=1)
    x_val["prediction"] = x_val[columns].apply(get_prediction, axis=1)

    # Save the dataframes to local disk.
    x_train.to_csv(f"{local_path}data/reference.csv")
    x_val.to_csv(f"{local_path}data/current.csv")
    logging.info(
        "x_train and x_val dataframes are saved to the local disk as \
            'reference' and 'current' csv files, respectively."
    )

    # Put the dataframes in S3 bucket also
    put_object(
        f"{local_path}data/reference.csv", bucket, "data/reference.csv", "Name", "data"
    )
    put_object(
        f"{local_path}data/current.csv", bucket, "data/current.csv", "Name", "data"
    )
    logging.info(
        "x_train and x_val dataframes are saved to the S3 bucket '%s' as 'data/reference' \
            and 'data/current' csv files, respectively.",
        bucket,
    )

    return x_train


def create_evidently_reports() -> list[Any]:

    """
    Creates and saves evidently dashboards as html.
    """

    # Retrieve variables
    bucket, _, local_path, _, _, _, _ = get_vars()

    reference = pd.read_csv(f"{local_path}data/reference.csv")
    current = pd.read_csv(f"{local_path}data/current.csv")

    # Dashboards we need
    dashboards = {
        "data_drift_dashboard": DataDriftTab(),
        "data_target_drift_dashboard": NumTargetDriftTab(),
        "regression_model_performance_dashboard": RegressionPerformanceTab(),
        "data_quality_dashboard": DataQualityTab(),
    }

    # Create and save dashboards
    for key, value in dashboards.items():

        dashboard = Dashboard(tabs=[value])
        dashboard.calculate(reference, current, column_mapping=column_mapping)
        file_path = f"{local_path}web-flask/templates/{key}.html"
        dashboard.save(file_path)
        put_object(file_path, bucket, f"evidently/reports/{key}.html", "Name", "report")
        logging.info(
            "Dashboard '%s' is created and saved on the local disk and put in S3 bucket.",
            key,
        )

    return list(dashboards.keys())


def send_email(
    flag: int, drifts: list[tuple[str, float, Literal[True, False]]]
) -> None:

    """
    Sends data drift results via AWS SNS.
    """

    # AWS SNS arguments
    topic_arn = get_parameter("sns_topic_arn")
    subject = "Data drift results"

    # SNS message depending on whether data drift exists
    if flag == 0:
        message = f"No data drift has been detected. Results are: {drifts}"
    else:
        message = f"{flag} data drift(s) is/are detected. Results are: {drifts}"

    # Send the notification
    send_sns_topic_message(topic_arn, message, subject)

    logging.info(
        "Email about the data drift results are sent to AWS SNS topic 'WaiterTipTopic'."
    )


def evaluate_data_drift(ti: Any) -> List[tuple[str, float, Literal[True, False]]]:

    """
    Evaluates data drifts and checks how many of them exist if any.
    """

    # Retrieve variables
    _, _, local_path, _, _, _, _ = get_vars()

    reference = pd.read_csv(f"{local_path}data/reference.csv")
    current = pd.read_csv(f"{local_path}data/current.csv")

    # Create and save the data drift profile as json
    data_drift_profile = Profile(sections=[DataDriftProfileSection()])
    data_drift_profile.calculate(reference, current, column_mapping=column_mapping)
    report = data_drift_profile.json()

    # Convert to python dictionary
    report = json.loads(report)

    logging.info("Data drift profile is created and stored as a python dictionary.")

    # Store features and their drift scores, and flag any data drift
    drifts = []
    flag = 0
    for feature in (
        column_mapping.numerical_features + column_mapping.categorical_features
    ):
        drift_score = report["data_drift"]["data"]["metrics"][feature]["drift_score"]
        drift_detected = report["data_drift"]["data"]["metrics"][feature][
            "drift_detected"
        ]
        drifts.append((feature, round(drift_score, 3), drift_detected))
        if drift_detected is True:
            flag += 1
    logging.info("%s data drift(s) is/are detected.", flag)

    # Send email about data drift by AWS SNS
    send_email(flag, drifts)

    # Push the results to XCom
    ti.xcom_push(key="drifts", value=drifts)
    logging.info("Data drift evaluation results '%s' are pushed to XCom.", drifts)


def record_metrics(ti: Any, tag: str) -> None:

    """
    Records data drift evaluation results in MLFlow,
    allowing them to be displayed on Grafana.
    """

    from datetime import datetime

    import mlflow

    # Retrieve variables
    _, _, _, _, _, experiment_name, _ = get_vars()

    # We store variables that won't change often in AWS Parameter Store.
    tracking_server_host = get_parameter(
        "tracking_server_host"
    )  # This can be local: 127.0.0.1 or EC2, e.g.: ec2-54-75-5-9.eu-west-1.compute.amazonaws.com.

    # Set the tracking server uri
    evidently_port = 5500
    evidently_tracking_uri = f"http://{tracking_server_host}:{evidently_port}"
    mlflow.set_tracking_uri(evidently_tracking_uri)

    # Create an mlflow experiment
    mlflow.set_experiment(experiment_name)

    # Get the data drift evaluation results
    metrics = ti.xcom_pull(key="drifts", task_ids=["evaluate_data_drift"])
    metrics = metrics[0]
    logging.info("Data drift metrics '%s' are retrieved from XCom.", metrics)

    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d / %H-%M-%S")
    logging.info("Date/time '%s' is set.", date_time)

    with mlflow.start_run() as run:

        # Set a tag
        mlflow.set_tag("model", tag)

        # Log parameters
        mlflow.log_param("record_date", date_time)

        for feature in metrics:
            mlflow.log_metric(feature[0], round(feature[1], 3), feature[2])

        logging.info("MLFlow run: %s", run.info)


def monitor_evidently(flag=0) -> Union[None, Dict[str, Any]]:

    """
    Initiates Evidently monitoring, and computes the data metrics.
    """

    # Retrieve variables
    _, _, local_path, _, _, _, _ = get_vars()

    reference = pd.read_csv(f"{local_path}data/reference.csv")
    current = pd.read_csv(f"{local_path}data/current.csv")

    metrics = {}
    registry = pc.CollectorRegistry()

    # Monitoring program
    evidently_monitoring = ModelMonitoring(
        monitors=[
            NumTargetDriftMonitor(),
            DataDriftMonitor(),
            RegressionPerformanceMonitor(),
            DataQualityMonitor(),
        ],
        options=None,
    )

    # Monitoring results
    evidently_monitoring.execute(
        reference_data=reference, current_data=current, column_mapping=column_mapping
    )
    results = evidently_monitoring.metrics()
    logging.info("Data metrics were found by Evidently.")

    for i, (metric, value, labels) in enumerate(results, start=1):

        if labels:
            label = "_".join(list(labels.values()))
        else:
            label = "na"

        try:
            metric_key = f"evidently:{metric.name}:{label}"
            prom_metric = pc.Gauge(metric_key, "", registry=registry)
            prom_metric.set(value)
            metrics[f"evidently_{i}"] = prom_metric
        except:
            pass

    logging.info(
        "Evidently data metrics were translated to Prometheus for \
            querying and displaying them on Prometheus and Grafana."
    )

    # Save the dictionary as a text file in the local disk
    with open(f"{local_path}data/metrics.txt", "w", encoding="utf-8") as outfile:
        for key, value in metrics.items():
            element = (
                f"{str(key)}: pc.metrics.Gauge({str(value).replace('gauge:', '')})\n"
            )
            outfile.write(element)
    logging.info("Data metrics are saved on the local disk as a text file.")

    if flag != 0:
        return metrics

    return None

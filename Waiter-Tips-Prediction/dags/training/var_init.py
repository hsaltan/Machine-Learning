"""
    This module sets the variables and stores them on Airflow.

    This script requires that `airflow` be installed within the Python environment you are
    running this script in.

    The script sets the variables for experiment and model names, and the local and S3 path
    to the data by receiving input from the user or using pre-established ones. It stores the
    newly defined variables on Airflow.

    This file can also be imported as a module and contains the following
    functions:

        * define_variables - takes user input for experiment, model and path variables or allows
        to continue with the current ones, and registers all of them in Airflow.
"""

# Import libraries
import json
import logging
from datetime import datetime

from airflow.models import Variable


def define_variables(
    mlf_dict: dict, s3_dict: dict, local_dict: dict
) -> tuple[str, str, str]:

    """
    Takes new experiment and/or model variables
    as user input or allows to continue with the
    current ones. Sets the S3 and local path
    variables. Registers all of them in Airflow.
    """

    date_time = datetime.now().strftime("%Y-%m-%d / %H-%M-%S")
    logging.info("Date/time '%s' is set.", date_time)

    # User input
    mlflow_experiment_name_input = mlf_dict["mlflow_experiment_name"]
    evidently_experiment_name_input = mlf_dict["evidently_experiment_name"]
    model_name_input = mlf_dict["model_name"]
    logging.info(
        "User input for mlflow experiment as '%s', evidenly experiment as '%s'\
        and model as '%s' are received.",
        mlflow_experiment_name_input,
        evidently_experiment_name_input,
        model_name_input,
    )

    # Get existing parameters if they exist. If not, create variables and assign them a
    # value based on date/time.
    try:
        temp_dict = Variable.get("mlflow_dict", deserialize_json=True)
    except Exception:
        print("We don't have any variables defined on Airflow yet.")

    try:
        mlflow_experiment_name = temp_dict["mlflow_experiment_name"]
    except Exception:
        mlflow_experiment_name = f"mlflow-experiment-{date_time}"
        print("We don't have any 'mlflow experiment' variable defined on Airflow.")
        print(
            "A new variable name '%s' is created for the experiment.",
            mlflow_experiment_name,
        )

    try:
        evidently_experiment_name = temp_dict["evidently_experiment_name"]
    except Exception:
        evidently_experiment_name = f"evidently-experiment-{date_time}"
        print("We don't have any 'evidently experiment' variable defined on Airflow.")
        print(
            "A new variable name '%s' is created for the experiment.",
            evidently_experiment_name,
        )

    try:
        model_name = temp_dict["model_name"]
    except Exception:
        model_name = f"tip-advisor-{date_time}"
        print("We don't have any 'model' variable defined on Airflow.")
        print("A new variable name '%s' is created for the model.", model_name)

    #  Compare variables with the user input. User input overrides the existing parameters.
    mlflow_dict = {}

    if mlflow_experiment_name_input:
        mlflow_dict["mlflow_experiment_name"] = mlflow_experiment_name_input
    else:
        mlflow_dict["mlflow_experiment_name"] = mlflow_experiment_name

    if evidently_experiment_name_input:
        mlflow_dict["evidently_experiment_name"] = evidently_experiment_name_input
    else:
        mlflow_dict["evidently_experiment_name"] = evidently_experiment_name

    if model_name_input:
        mlflow_dict["model_name"] = model_name_input
    else:
        mlflow_dict["model_name"] = model_name

    # Serialize and save/update mlflow_dict in Airflow variables.
    mlflow_json_object = json.dumps(mlflow_dict, indent=2)
    Variable.set(
        "mlflow_dict",
        mlflow_json_object,
        description="Mlflow variable names for 'experiment' and 'model'",
    )
    logging.info(
        "Variables that are stored in the dictionary as '%s' are saved in Airflow.",
        mlflow_dict,
    )

    # Serialize and save/update s3_dict in Airflow variables.
    s3_json_object = json.dumps(s3_dict, indent=2)
    Variable.set(
        "s3_dict",
        s3_json_object,
        description="S3 variable names for 'bucket' and 'key'",
    )
    logging.info(
        "Variables that are stored in the dictionary as '%s' are saved in Airflow.",
        s3_dict,
    )

    # Serialize and save/update local_dict in Airflow variables.
    local_json_object = json.dumps(local_dict, indent=2)
    Variable.set(
        "local_dict", local_json_object, description="Local system variable names"
    )
    logging.info(
        "Variables that are stored in the dictionary as '%s' are saved in Airflow.",
        local_dict,
    )

    return (
        mlflow_dict["mlflow_experiment_name"],
        mlflow_dict["evidently_experiment_name"],
        mlflow_dict["model_name"],
    )

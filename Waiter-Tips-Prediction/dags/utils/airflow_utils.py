"""
    This module enables to get variables from Airflow.

    This script requires that `airflow` be installed within the Python environment you are
    running this script in.

    The script helps retrieving the variables established and stored on Airflow earlier for
    later use in other modules.

    This file can also be imported as a module and contains the following
    functions:

        * get_vars - returns all variables created and stored on Airflow Variables.
"""

# Import libraries
import logging
from typing import List

from airflow.models import Variable


def get_vars() -> List[str]:

    """
    Returns all variables created and stored on
    Airflow Variables.
    """

    # Retrieve the s3_dict variable
    s3_dict = Variable.get("s3_dict", deserialize_json=True)
    bucket = s3_dict["bucket_name"]
    file_name = s3_dict["key"]
    logging.info("Airflow variable dictionary stored as'%s' is retrieved.", s3_dict)

    # Retrieve the local_dict variable
    local_dict = Variable.get("local_dict", deserialize_json=True)
    local_path = local_dict["current_dir"]
    try:
        local_data_transformed_filename = local_dict["local_data_transformed_filename"]
    except Exception:
        local_data_transformed_filename = None
    logging.info("Airflow variable dictionary stored as'%s' is retrieved.", local_dict)

    # Retrieve the mlflow_dict variable
    mlflow_dict = Variable.get("mlflow_dict", deserialize_json=True)
    mlflow_experiment_name = mlflow_dict["mlflow_experiment_name"]
    evidently_experiment_name = mlflow_dict["evidently_experiment_name"]
    model_name = mlflow_dict["model_name"]
    logging.info("Airflow variable dictionary stored as'%s' is retrieved.", mlflow_dict)

    return (
        bucket,
        file_name,
        local_path,
        local_data_transformed_filename,
        mlflow_experiment_name,
        evidently_experiment_name,
        model_name,
    )

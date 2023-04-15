"""
    This module trains tha data, finds the best parameters and registers the best model.

    This script requires that `numpy`, `mlflow`, `xgboost`, `hyperopt`, and `sklearn` be
    installed within the Python environment you are running this script in. `aws_utils`,
    `airflow_utils` and `mlflow_utils` are util modules created with this script,
    which also needs be loaded.

    The script trains the data with Hyperopt to search for the optimal parameters, runs the
    model with these parameters again, and registers the model in MLFlow, then replaces the
    production model if the former outperforms the latter. Finally, it goes over all
    experiments made so far, finds the one that has resulted in the lowest loss value, and
    notifies the user.

    This file can also be imported as a module and contains the following
    functions:

        * search_best_parameters - searches for the optimum parameters within the defined ranges
        * find_best_params - retrieves the parameters of the best model run of a particular
        experiment
        * run_best_model - runs the model with the best parameters, saves the model and the
        artifacts
        * register_best_model - registers the best run id
        * test_model - calculates and compares RMSEs of the staging and production models
        * compare_models - Compares the new model and the production model, and makes transitions
        * get_experiments_by_id - lists all existing experiments and finds their ids
        * get_top_run - checks all runs in all experiments and finds the best run
"""

# Import libraries
import json
import logging
import pickle
from datetime import datetime
from typing import Any, Literal, Union

import mlflow
import numpy as np
import xgboost as xgb
from hyperopt import STATUS_OK, Trials, fmin, hp, tpe
from hyperopt.pyll import scope
from mlflow.tracking import MlflowClient
from numpy import loadtxt
from sklearn.metrics import mean_squared_error
from ..utils.airflow_utils import get_vars
from ..utils.aws_utils import create_parameter, get_parameter, send_sns_topic_message
from ..utils.mlflow_utils import (
    delete_version,
    get_best_params,
    get_latest_version,
    list_experiments,
    load_models,
    register_model,
    search_runs,
    transition_to_stage,
    update_model_version,
    update_registered_model,
    wait_until_ready,
)

# from utils.airflow_utils import get_vars
# from utils.aws_utils import create_parameter, get_parameter, send_sns_topic_message
# from utils.mlflow_utils import (
#     delete_version,
#     get_best_params,
#     get_latest_version,
#     list_experiments,
#     load_models,
#     register_model,
#     search_runs,
#     transition_to_stage,
#     update_model_version,
#     update_registered_model,
#     wait_until_ready,
# )

# We store variables that won't change often in AWS Parameter Store.
tracking_server_host = get_parameter(
    "tracking_server_host"
)  # This can be local: 127.0.0.1 or EC2, e.g.: ec2-54-75-5-9.eu-west-1.compute.amazonaws.com.

# Set the tracking server uri
MLFLOW_PORT = 5000
mlflow_tracking_uri = f"http://{tracking_server_host}:{MLFLOW_PORT}"
mlflow.set_tracking_uri(mlflow_tracking_uri)

mlflow_client = MlflowClient(mlflow_tracking_uri)

# Retrieve the initial path and mlflow artifact path from AWS Parameter Store.
try:
    mlflow_artifact_path = json.loads(get_parameter("artifact_paths"))[
        "mlflow_model_artifacts_path"
    ]  # models_mlflow
    mlflow_initial_path = json.loads(get_parameter("initial_paths"))[
        "mlflow_model_initial_path"
    ]  # s3://s3b-tip-predictor/mlflow/
except:
    mlflow_artifact_path = "models_mlflow"
    mlflow_initial_path = "s3://s3b-tip-predictor/mlflow/"


def search_best_parameters(tag: str) -> dict[str, Union[int, float]]:

    """
    Searches and finds the optimum parameters within the
    defined ranges with Hyperopt. Logs them in MLFlow.
    """

    # Retrieve variables
    _, _, local_path, _, experiment_name, _, _ = get_vars()

    # Load data from the local disk
    x_train = loadtxt(f"{local_path}data/X_train.csv", delimiter=",")
    x_val = loadtxt(f"{local_path}data/X_val.csv", delimiter=",")
    y_train = loadtxt(f"{local_path}data/y_train.csv", delimiter=",")
    y_val = loadtxt(f"{local_path}data/y_val.csv", delimiter=",")
    logging.info(
        "Training and validation datasets are retrieved from the local storage."
    )

    # Convert to DMatrix data structure for XGBoost
    train = xgb.DMatrix(x_train, label=y_train)
    valid = xgb.DMatrix(x_val, label=y_val)
    logging.info("Training and validation matrix datasets are created for XGBoost.")

    # Set an mlflow experiment
    mlflow.set_experiment(experiment_name)
    logging.info(
        "Tracking server host '%s' is retrieved from AWS Parameter Store.",
        tracking_server_host,
    )
    logging.info("Tracking uri '%s' is set in mlflow.", mlflow_tracking_uri)
    logging.info("Check the tracking uri: '%s'", mlflow.get_tracking_uri())
    logging.info("MLFlow experiment '%s' is set.", experiment_name)

    # Search for best parameters
    def objective(params: dict) -> dict[str, Union[float, Literal["ok"]]]:

        with mlflow.start_run():

            mlflow.set_tag("model", tag)
            mlflow.log_params(params)

            booster = xgb.train(
                params=params,
                dtrain=train,
                num_boost_round=100,
                evals=[(valid, "validation")],
                early_stopping_rounds=50,
            )

            y_pred = booster.predict(valid)
            rmse = mean_squared_error(y_val, y_pred, squared=False)
            mlflow.log_metric("rmse", rmse)

        logging.info("Loss: %s and status: %s", rmse, STATUS_OK)

        return {"loss": rmse, "status": STATUS_OK}

    # Search space for parameters
    search_space = {
        "max_depth": scope.int(hp.quniform("max_depth", 4, 100, 1)),
        "learning_rate": hp.loguniform("learning_rate", -3, 0),
        "colsample_bytree": hp.choice("colsample_bytree", np.arange(0.3, 0.8, 0.1)),
        "subsample": hp.uniform("subsample", 0.8, 1),
        "n_estimators": 100,
        "reg_lambda": hp.loguniform("reg_lambda", -6, -1),
        "min_child_weight": hp.loguniform("min_child_weight", -1, 3),
        "objective": "reg:squarederror",
        "seed": 42,
    }

    best_result = fmin(
        fn=objective,
        space=search_space,
        algo=tpe.suggest,
        max_evals=10,  # 50
        trials=Trials(),
    )

    logging.info("Best result: %s", best_result)

    return best_result


def find_best_params(ti: Any, metric: str, max_results: int) -> dict[str, Any]:

    """
    Retrieves the parameters of the best model run of a particular experiment
    from the mlflow utils module.
    """

    # Retrieve variables
    _, _, _, _, experiment_name, _, _ = get_vars()

    # Get the best params from mlflow server
    best_params = get_best_params(mlflow_client, experiment_name, metric, max_results)
    logging.info(
        "The resulting best parameters of the experiment '%s' by the metric '%s' are: %s",
        experiment_name,
        metric,
        best_params,
    )

    # Push the best params to XCom
    ti.xcom_push(key="best_params", value=best_params)
    logging.info(
        "The resulting best parameters '%s' of the experiment '%s' are pushed to XCom.",
        best_params,
        experiment_name,
    )

    return best_params


def run_best_model(ti: Any, tag: str) -> str:

    """
    Runs the model with the best parameters searched and found
    at the earlier phase. Then, saves the model and info in the artifacts
    folder or bucket.
    """

    # Retrieve variables
    _, _, local_path, _, experiment_name, _, model_name = get_vars()

    best_params = ti.xcom_pull(key="best_params", task_ids=["find_best_params"])
    best_params = best_params[0]
    logging.info("Best params '%s' are retrieved from XCom.", best_params)

    logging.info(
        "MLFlow artifact path '%s' is retrieved from AWS Parameter Store.",
        mlflow_artifact_path,
    )

    # Load data from the local disk.
    x_train = loadtxt(f"{local_path}data/X_train.csv", delimiter=",")
    x_val = loadtxt(f"{local_path}data/X_val.csv", delimiter=",")
    y_train = loadtxt(f"{local_path}data/y_train.csv", delimiter=",")
    y_val = loadtxt(f"{local_path}data/y_val.csv", delimiter=",")
    logging.info(
        "Training and validation datasets are retrieved from the local storage."
    )

    # Convert to DMatrix data structure for XGBoost.
    train = xgb.DMatrix(x_train, label=y_train)
    valid = xgb.DMatrix(x_val, label=y_val)
    logging.info("Training and validation matrix datasets are created for XGBoost.")

    # Set an mlflow experiment
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run() as run:

        # Get the run_id of the best model
        best_run_id = run.info.run_id
        logging.info("Best run id: '%s'", best_run_id)

        mlflow.set_tag("model", tag)
        mlflow.log_params(best_params)

        # Train the XGBoost model with the best parameters
        booster = xgb.train(
            params=best_params,
            dtrain=train,
            num_boost_round=100,
            evals=[(valid, "validation")],
            early_stopping_rounds=50,
        )

        y_pred = booster.predict(valid)
        rmse = mean_squared_error(y_val, y_pred, squared=False)
        mlflow.log_metric("rmse", rmse)

        # Save the model (xgboost_model.bin) locally in the folder "../models/" (in case we want)
        with open(f"{local_path}models/xgboost_model.bin", "wb") as f_out:
            pickle.dump(booster, f_out)
        logging.info(
            "XGBoost model is saved on the path '%smodels/xgboost_model.bin' of the local machine.",
            local_path,
        )

        # Save the model (xgboost_model.bin) using 'log_artifact' in the defined artifacts
        # folder/bucket (in case we want). This is defined on the CLI and as artifact path
        # parameter on AWS Parameter Store: s3://s3b-tip-predictor/mlflow/ ... /models_mlflow/
        mlflow.log_artifact(
            local_path=f"{local_path}models/xgboost_model.bin",
            artifact_path=mlflow_artifact_path,
        )
        logging.info(
            "Artifacts are saved on the artifact path '%s'.", mlflow_artifact_path
        )

        # Save the model (booster) using 'log_model' in the defined artifacts folder/bucket
        # This is defined on the CLI and as artifact path parameter on AWS Parameter Store:
        # s3://s3b-tip-predictor/mlflow/ ... /models_mlflow/
        mlflow.xgboost.log_model(booster, artifact_path=mlflow_artifact_path)
        logging.info(
            "XGBoost model is saved on the artifact path '%s'.", mlflow_artifact_path
        )
        logging.info("Default artifacts URI: '%s'", mlflow.get_artifact_uri())

        # Push the best run id to XCom
        ti.xcom_push(key="best_run_id", value=best_run_id)
        logging.info(
            "The best run id '%s' of the model '%s' is pushed to XCom.",
            best_run_id,
            model_name,
        )


def register_best_model(ti: Any, version_description: str) -> dict[str, Any]:

    """
    Registers the best run id, adds a high-level and version
    descriptions, and transitions the model to 'staging'.
    """

    # Retrieve variables
    _, _, _, _, _, _, model_name = get_vars()

    # Get the best run id
    best_run_id = ti.xcom_pull(key="best_run_id", task_ids=["run_best_model"])
    best_run_id = best_run_id[0]
    logging.info("Best run id '%s' is retrieved from XCom.", best_run_id)

    # Register the best model
    model_details = register_model(best_run_id, mlflow_artifact_path, model_name)
    logging.info(
        "Model '%s' with the run id '%s' is registered on artifact path '%s'.",
        model_name,
        best_run_id,
        mlflow_artifact_path,
    )

    # Wait until the model is ready
    wait_until_ready(mlflow_client, model_details.name, model_details.version)
    logging.info("Model '%s' is ready for further processing.", model_name)

    # Add a high-level description to the registered model, including the machine
    # learning problem and dataset
    description = """
        This model predicts the tips given to the waiters for serving the food.
        Waiter Tips data consists of six features:
            1. total_bill,
            2. sex (gender of the customer),
            3. smoker (whether the person smoked or not),
            4. day (day of the week),
            5. time (lunch or dinner),
            6. size (number of people in a table)
        """
    update_registered_model(mlflow_client, model_details.name, description)
    logging.info(
        "A high-level description '%s' is added to the model '%s'.",
        description,
        model_name,
    )

    # Add a model version description with information about the model architecture and
    # machine learning framework
    update_model_version(
        mlflow_client, model_details.name, model_details.version, version_description
    )
    logging.info(
        "A version description '%s' is added to the model '%s'.",
        version_description,
        model_name,
    )

    # Transition the model to Staging
    transition_to_stage(
        mlflow_client, model_details.name, model_details.version, "staging", False
    )
    logging.info("Model '%s' is transitioned to 'staging'.", model_name)

    # Push model details to XCom
    model_details_dict = {}
    model_details_dict["model_name"] = model_details.name
    model_details_dict["model_version"] = model_details.version
    ti.xcom_push(key="model_details", value=model_details_dict)
    logging.info(
        "Model details '%s' of the registered model '%s' is pushed to XCom.",
        model_details_dict,
        model_name,
    )


def test_model(ti: Any) -> dict[str, float]:

    """
    Calculates RMSE for each of the new model that is developed
    and transitioned to 'staging', and the previous model that is
    already in the 'production' stage. Allows for comparison of
    both models.
    """

    # Retrieve variables
    _, _, local_path, _, _, _, model_name = get_vars()

    # Get model details from XCom
    model_details_dict = ti.xcom_pull(
        key="model_details", task_ids=["register_best_model"]
    )
    model_details_dict = model_details_dict[0]
    model_name = model_details_dict["model_name"]
    logging.info("Model details '%s' are retrieved from XCom.", model_details_dict)

    # Load data from the local disk
    x_test = loadtxt(f"{local_path}data/X_val.csv", delimiter=",")
    y_test = loadtxt(f"{local_path}data/y_val.csv", delimiter=",")
    logging.info("Validation datasets are retrieved from the local storage.")

    # Load the staging model, predict with the new data and calculate its RMSE
    model_staging = load_models(model_name, "staging")
    model_staging_predictions = model_staging.predict(x_test)
    model_staging_rmse = mean_squared_error(
        y_test, model_staging_predictions, squared=False
    )
    logging.info("model_staging_rmse: %s", model_staging_rmse)

    try:
        # Load the production model, predict with the new data and calculate its RMSE
        model_production = load_models(model_name, "production")
        model_production_predictions = model_production.predict(x_test)
        model_production_rmse = mean_squared_error(
            y_test, model_production_predictions, squared=False
        )
        logging.info("model_production_rmse: %s", model_production_rmse)

    except Exception:
        print(
            "It seems that there is not any model in the production stage yet. \
                Then, we transition the current model to production."
        )
        model_production_rmse = None

    rmse_dict = {}
    rmse_dict["model_production_rmse"] = model_production_rmse
    rmse_dict["model_staging_rmse"] = model_staging_rmse

    # Push the RMSEs of the staging and production models to XCom
    ti.xcom_push(key="rmses", value=rmse_dict)
    logging.info(
        "RMSEs of the staging and production models '%s' are pushed to XCom.", rmse_dict
    )


def compare_models(ti: Any) -> None:

    """
    Based on the RMSEs of the models, compares which one yields less
    loss value. The one with lower RMSE will be in 'production' stage.
    The other with higher RMSE will either stay in 'staging' (if new model)
    or be transitioned to 'archive' (if previous model) after which an
    optional deletion is to be offered.
    """

    # Get rmse_dict from XCom
    rmse_dict = ti.xcom_pull(key="rmses", task_ids=["test_model"])
    rmse_dict = rmse_dict[0]
    model_production_rmse = rmse_dict["model_production_rmse"]
    model_staging_rmse = rmse_dict["model_staging_rmse"]
    logging.info(
        "RMSEs of the staging and production models '%s' are retrieved from XCom.",
        rmse_dict,
    )

    # Get model details from XCom
    model_details_dict = ti.xcom_pull(
        key="model_details", task_ids=["register_best_model"]
    )
    model_details_dict = model_details_dict[0]
    model_name = model_details_dict["model_name"]
    model_version = model_details_dict["model_version"]
    logging.info("Model details '%s' are retrieved from XCom.", model_details_dict)

    # Compare RMSEs
    # If there is a model in production stage already
    if model_production_rmse:

        # If the staging model's RMSE is lower than or equal to the production model's
        # RMSE, transition the former model to production stage, and delete the previous
        # production model.
        if model_staging_rmse <= model_production_rmse:
            transition_to_stage(
                mlflow_client, model_name, model_version, "production", True
            )
            latest_stage_version = get_latest_version(
                mlflow_client, model_name, "archived"
            )
            delete_version(mlflow_client, model_name, latest_stage_version)
    else:
        # If there is not any model in production stage already, transition the staging
        # model to production
        transition_to_stage(
            mlflow_client, model_name, model_version, "production", False
        )


def get_experiments_by_id() -> list[str]:

    """
    Lists all existing experiments and finds their ids.
    """

    # List of existing experiments
    experiments = list_experiments(mlflow_client)
    logging.info("Experiments '%s' are retrieved from MLFlow.", experiments)
    experiment_ids = [experiment.experiment_id for experiment in experiments]

    # Remove default experiment as it has no runs
    experiment_ids.remove("0")

    return experiment_ids


def get_top_run(metric: str) -> dict[str, Union[str, float]]:

    """
    Checks all runs in all experiments and finds the
    best run that returns the lowest loss value.
    """

    best_rmse_dict = {}

    # A very high error score as the baseline
    best_run_score = 1_000_000

    # List of existing experiment ids
    experiment_ids = get_experiments_by_id()
    logging.info("Experiments by ids '%s' are available.", experiment_ids)

    for experiment_id in experiment_ids:

        try:
            # Best run of a particular experiment
            runs = search_runs(mlflow_client, experiment_id, metric, 10000)
            best_run_id = runs[0].info.run_id
            best_run_rmse = runs[0].data.metrics["rmse"]
            logging.info(
                "Experiment by id '%s' has the best run by id '%s' with the rmse score %s.",
                experiment_id,
                best_run_id,
                best_run_rmse,
            )

            # If the experiment has the best score, we store it.
            if best_run_rmse <= best_run_score:
                best_run_score = best_run_rmse
                best_rmse_dict["experiment_id"] = experiment_id
                best_rmse_dict["best_run_id"] = best_run_id
                best_rmse_dict["best_run_rmse"] = best_run_rmse
                logging.info(
                    "As of now, the run by id '%s' of the experiment by id '%s' has the \
                        best historical rmse score %s among all experiments' runs.",
                    best_run_id,
                    experiment_id,
                    best_run_rmse,
                )
        except Exception:
            print("Experiment by id '%s' has no runs at all.", experiment_id)

    # Build the path to the best model
    experiment_id = best_rmse_dict["experiment_id"]
    best_run_id = best_rmse_dict["best_run_id"]
    logged_model = f"{mlflow_initial_path}{experiment_id}/{best_run_id}/artifacts/{mlflow_artifact_path}/"
    logging.info(
        "The best historical model is given by the run '%s' of the experiment '%s'.",
        best_run_id,
        experiment_id,
    )

    # Create a parameter on AWS from the best model info to enable the prediction script to
    # use it later
    create_parameter("logged_model", "Path to the best model", logged_model, "String")
    logging.info("The best historical model is logged to '%s'.", logged_model)

    # Set the current date and time
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d / %H-%M-%S")
    logging.info("Date/time '%s' is set.", date_time)

    # Send an email about the final result.
    topic_arn = get_parameter("sns_topic_arn")
    subject = "Waiter tip prediction training results "
    message = f"As a result of the latest training performed on '{date_time}',\n\nthe best historical model is provided by the run '{best_run_id}' of the experiment '{experiment_id}',\n\nand it has a RMSE of {best_rmse_dict['best_run_rmse']}."
    send_sns_topic_message(topic_arn, message, subject)
    logging.info(
        "Email about the training results are sent to AWS SNS topic 'WaiterTipTopic'."
    )

    return best_rmse_dict

"""
    This module allows for working on MLFlow.

    This script requires that `mlflow` be installed within the Python environment you are
    running this script in.

    The script gets experiments and their ids, searches for runs and finds the best
    parameters, registers, updates, transitions, and loads the models, finds the latest
    version, and deletes a specific version of the model.

    This file can also be imported as a module and contains the following
    functions:

        * transition_to_stage - transitions a model to a defined stage
        * load_models - loads the latest model saved before
        * get_latest_version - finds the version number of the latest version of a model in a
        particular stage
        * delete_version - deletes a specific version of a model permanently
        * update_model_version - adds a description to a version of the model
        * update_registered_model - adds a description to the registered model
        * wait_until_ready -  waits until the model is ready
        * register_model - registers the model
        * list_experiments - gets all existing experiments
        * get_experiment_id - finds the experiment id of a specific experiment by its name
        * search_runs - searches and brings all info pertaining to a specific experiment's runs
        * get_best_params - gets the parameters of the best model run of a particular experiment
"""

# Import libraries
from typing import Any

import mlflow
from mlflow.entities import ViewType
from mlflow.entities.model_registry.model_version_status import ModelVersionStatus
from mlflow.tracking import MlflowClient


def transition_to_stage(
    client: MlflowClient,
    model_name: str,
    model_version: str,
    new_stage: str,
    archive: bool,
) -> None:

    """
    Transitions a model to a defined stage.
    """

    # Transition the model to the stage
    client.transition_model_version_stage(
        name=model_name,
        version=model_version,
        stage=new_stage,
        archive_existing_versions=archive,
    )

    print(
        "Version '%s' of the model '%s' has been transitioned to '%s'.",
        model_version,
        model_name,
        new_stage,
    )
    print("\n")


def load_models(model_name: str, stage: str) -> Any:

    """
    Loads the latest model saved before given the model name and stage.
    """

    # Get the model in the stage
    model_stage_uri = f"models:/{model_name}/{stage}"
    print(
        "Loading registered '%s' model version from URI: '%s'", stage, model_stage_uri
    )
    print("\n")

    model = mlflow.pyfunc.load_model(model_stage_uri)

    return model


def get_latest_version(client: MlflowClient, model_name: str, stage: str) -> str:

    """
    Finds the version number of the latest version of a model in a particular stage.
    """

    # Get the information for the latest version of the model in a given stage
    latest_version_info = client.get_latest_versions(model_name, stages=[stage])
    latest_stage_version = latest_version_info[0].version

    print(
        "The latest '%s' version of the model '%s' is '%s'.",
        stage,
        model_name,
        latest_stage_version,
    )
    print("\n")

    return latest_stage_version


def delete_version(client: MlflowClient, model_name: str, model_version: str) -> None:

    """
    Deletes a specific version of a model permanently.
    """

    client.delete_model_version(
        name=model_name,
        version=model_version,
    )

    print(
        "The version '%s' of the model '%s' has been permanently deleted.",
        model_version,
        model_name,
    )
    print("\n")


def update_model_version(
    client: MlflowClient, model_name: str, model_version: str, version_description: str
) -> str:

    """
    Adds a description to a version of the model.
    """

    response = client.update_model_version(
        name=model_name, version=model_version, description=version_description
    )

    run_id = response.run_id

    print(
        "Description has been added to the version '%s' of the model '%s'.",
        model_version,
        model_name,
    )
    print("\n")

    return run_id


def update_registered_model(
    client: MlflowClient, model_name: str, description: str
) -> str:

    """
    Adds a description to the model.
    """

    response = client.update_registered_model(name=model_name, description=description)

    mod_name = response.name

    print("Description has been added to the model '%s'.", model_name)
    print("\n")

    return mod_name


def wait_until_ready(client: MlflowClient, model_name: str, model_version: str):

    """
    After creating a model version, it may take a short period of time to become ready.
    Certain operations, such as model stage transitions, require the model to be in the
    READY state. Other operations, such as adding a description or fetching model details,
    can be performed before the model version is ready (for example, while it is in the
    PENDING_REGISTRATION state).

    Uses the MlflowClient.get_model_version() function to wait until the model is ready.
    """

    status = "Not ready"

    while status == "Not ready":

        model_version_details = client.get_model_version(
            name=model_name,
            version=model_version,
        )

        status = ModelVersionStatus.from_string(model_version_details.status)
        print("Model status: %s", ModelVersionStatus.to_string(status))
        print("\n")


def register_model(
    best_run_id: str, artifact_path: str, model_name: str
) -> dict[str, Any]:

    """
    Registers the model.
    """

    # Register the model
    model_uri = f"runs:/{best_run_id}/{artifact_path}"
    model_details = mlflow.register_model(model_uri=model_uri, name=model_name)
    print("/n")
    print(
        "Version '%s' of the model '%s' has been registered.",
        model_details.version,
        model_details.name,
    )
    print("\n")
    print("Model details:", "\n", model_details, "\n")

    return model_details


def list_experiments(client: MlflowClient) -> list[dict]:

    """
    Gets all existing experiments
    """

    experiments = client.list_experiments()

    return experiments


def get_experiment_id(experiment_name: str) -> str:

    """
    Finds the experiment id of a specific experiment by its name.
    """

    # Find the experiment by name
    experiment = mlflow.get_experiment_by_name(experiment_name)

    # Get the id of the found experiment
    experiment_id = experiment.experiment_id

    return experiment_id


def search_runs(
    client: MlflowClient, experiment_id: str, order_by: str, max_results: int = 10000
) -> list[dict]:

    """
    Searches and brings all info of the runs belonging to a specific
    experiment which is introduced to the function by its id.
    """

    runs = client.search_runs(
        experiment_ids=[experiment_id],
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=max_results,
        order_by=[order_by],
    )

    return runs


def get_best_params(
    client: MlflowClient, experiment_name: str, order_by: str, max_results: int = 10000
) -> tuple[dict[str, Any], str]:

    """
    Gets the parameters of the best model run of a particular experiment.
    """

    # Get the id of the found experiment
    experiment_id = get_experiment_id(experiment_name)

    # Get the pandas data frame of the experiment results in the ascending order by RMSE
    runs = search_runs(client, experiment_id, order_by, max_results)

    # Get the id of the best run
    best_run_id = runs[0].info.run_id

    # Get the best model parameters
    best_params = runs[0].data.params
    rmse = runs[0].data.metrics["rmse"]
    print("\n")
    print(
        "Best parameters from the run '%s' of '%s/%s':",
        best_run_id,
        experiment_id,
        experiment_name,
    )
    print("\n")
    print("rmse:", rmse)
    for key, value in best_params.items():
        print("%s: %s", key, value)
    print("\n")

    return best_params

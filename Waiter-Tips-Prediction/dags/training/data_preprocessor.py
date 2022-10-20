"""
    This module prepares the data for training hot-encoding and splitting it as train
    and validation sets. It also updates the file path variable on Airflow and saves the
    transformed data on AWS S3.

    This script requires that `pandas`, `numpy`, and `sklearn` be installed within the
    Python environment you are running this script in. `aws_utils` and `airflow_utils` are
    util modules created with this script, which also needs be loaded.

    The script first retrieves the raw data from S3 using the variables stored on Airflow
    before, hot-encodes the feature set, splits the data as train and validation sets, and
    saves them on the local disk and S3 for further use. It stores the variable that sets
    the path of the transformed data on Airflow.

    This file can also be imported as a module and contains the following
    functions:

        * transform_data - imports data from the S3 bucket, transforms and saves it
        * split_data - splits the transformed data as training and validation sets.
"""

# Import libraries
import logging

from airflow.models import Variable
from utils.airflow_utils import get_vars
from utils.aws_utils import get_bucket_object, put_object


def transform_data() -> tuple[dict[str, str], str, int, int, int]:

    """
    Imports data from the S3 bucket and converts it into
    a pandas dataframe. Makes necessary transformations.
    Saves it into the local disk.
    """

    import json

    import pandas as pd

    # Retrieve the s3_dict variable
    bucket, file_name, local_path, _, _, _, _ = get_vars()
    original_file_name = file_name.split("/")[-1]

    # Read data from S3
    file, _ = get_bucket_object(bucket, file_name)
    logging.info("Data '%s' is retrieved from the S3 bucket '%s'.", file_name, bucket)

    # # Retrieve the local_dict variable
    local_dict = Variable.get("local_dict", deserialize_json=True)

    # Save the raw data locally
    local_data_filename = f"{local_path}data/{original_file_name}"
    data = pd.read_csv(file)
    data.to_csv(local_data_filename)
    logging.info(
        "Data '%s' is saved as '%s' on the local machine.",
        original_file_name,
        local_data_filename,
    )

    # Transform the data
    data_transformed = data.copy(deep=True)
    data_transformed["sex"] = data_transformed["sex"].map({"Female": 0, "Male": 1})
    data_transformed["smoker"] = data_transformed["smoker"].map({"No": 0, "Yes": 1})
    data_transformed["day"] = data_transformed["day"].map(
        {"Thur": 0, "Fri": 1, "Sat": 2, "Sun": 3}
    )
    data_transformed["time"] = data_transformed["time"].map({"Lunch": 0, "Dinner": 1})
    logging.info("Transformations are made on the data '%s'.", original_file_name)

    # Save it to the local disk as csv file
    transformed_file_name = "tips_transformed.csv"
    local_data_transformed_filename = f"{local_path}data/{transformed_file_name}"
    data_transformed.to_csv(local_data_transformed_filename)
    logging.info(
        "Data '%s' is saved as '%s' on the local machine.",
        transformed_file_name,
        local_data_transformed_filename,
    )

    # Serialize and update local_dict in Airflow variables.
    local_dict["local_data_transformed_filename"] = local_data_transformed_filename
    local_json_object = json.dumps(local_dict, indent=2)
    Variable.set(
        "local_dict", local_json_object, description="Local system variable names"
    )
    logging.info(
        "Variables that are stored in the dictionary as '%s' are saved in Airflow.",
        local_dict,
    )

    size_for_test = data_transformed.loc[data_transformed.index == 3, "size"].to_list()[
        0
    ]  # 2
    day_for_test = data_transformed.loc[data_transformed.index == 158, "day"].to_list()[
        0
    ]  # 3
    gender_for_test = data_transformed.loc[
        data_transformed.index == 216, "sex"
    ].to_list()[
        0
    ]  # 1

    return local_dict, bucket, size_for_test, day_for_test, gender_for_test


def split_data(test_size: float) -> tuple[int, int]:

    """
    Splits the data as training and validation sets.
    Saves them to the local disk and to the S3 bucket.
    """

    import glob

    import numpy as np
    import pandas as pd
    from numpy import savetxt
    from sklearn.model_selection import train_test_split

    # Retrieve variables
    bucket, file_name, local_path, local_data_transformed_filename, _, _, _ = get_vars()
    original_file_name = file_name.split("/")[-1]
    logging.info(
        "Data file path for '%s' is established as '%s'",
        local_data_transformed_filename.split("/")[-1],
        local_data_transformed_filename,
    )

    # Read data
    data_transformed = pd.read_csv(local_data_transformed_filename)

    # Features and label
    x_features = np.array(
        data_transformed[["total_bill", "sex", "smoker", "day", "time", "size"]]
    )
    y_label = np.array(data_transformed["tip"])

    # Train-test split
    x_train, x_val, y_train, y_val = train_test_split(
        x_features, y_label, test_size=test_size, random_state=42
    )
    logging.info(
        "Data is split as train (%s) and test (%s) sets.", (1 - test_size), test_size
    )

    # Save the datasets to the local disk
    files = {"x_train": x_train, "x_val": x_val, "y_train": y_train, "y_val": y_val}
    for key, value in files.items():
        savetxt(f"{local_path}data/{key}.csv", value, delimiter=",")
    logging.info(
        "Files '%s' are saved as csv files on the local disk.",
        ", ".join(list(files.keys())),
    )

    logging.info("Original file name is '%s'.", original_file_name)

    # Collect files saved in the local disk except the original file
    dir_path = f"{local_path}data/*"
    file_list = [file for file in glob.glob(dir_path) if original_file_name not in file]

    # Put all files (except the original file) to the S3 bucket also.
    for file in file_list:
        file_name = file.split("/")[-1]
        key = f"data/{file_name}"
        put_object(file, bucket, key, "Name", "data")
    logging.info(
        "Files '%s' are put in S3 bucket '%s/data'.", ", ".join(file_list), bucket
    )

    # For testing
    train_size = len(x_train)
    val_size = len(x_val)

    del files

    return train_size, val_size

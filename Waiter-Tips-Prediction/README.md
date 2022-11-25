# Waiter Tips Prediction

[![PyPI - Python Version](https://img.shields.io/badge/python-3.9-blue)](https://www.python.org/downloads/)
[![Boto3](https://img.shields.io/badge/boto3-1.24-purple)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
[![Evidently](https://img.shields.io/badge/evidently-0.1.58-ec0400)](https://www.evidentlyai.com/)
[![Prometheus](https://img.shields.io/badge/prometheus-0.15.0-e6522c)](https://prometheus.io/)
[![Apache Airflow](https://img.shields.io/badge/apache_airflow-2.4.2-00ad46)](https://airflow.apache.org/)
[![Flask](https://img.shields.io/badge/flask-2.1.3-B2B232)](https://flask.palletsprojects.com/en/2.2.x/)
[![Matplotlib](https://img.shields.io/badge/matplotlib-3.6.1-11557c)](https://matplotlib.org/)
[![Plotly](https://img.shields.io/badge/plotly-5.10.0-7a7aff)](https://plotly.com/)
[![Seaborn](https://img.shields.io/badge/seaborn-0.12.0-333663)](https://seaborn.pydata.org/)
[![Mlflow](https://img.shields.io/badge/mlflow-1.29.0-0093e1)](https://mlflow.org/)
[![Hyperopt](https://img.shields.io/badge/hyperopt-0.2.7-35a7e7)](https://hyperopt.github.io/hyperopt/)
[![Numpy](https://img.shields.io/badge/numpy-1.23.4-013243)](https://numpy.org/)
[![Pandas](https://img.shields.io/badge/pandas-1.5.0-130654)](https://pandas.pydata.org/)
[![Psycopg2](https://img.shields.io/badge/psycopg2-2.9.4-216464)](https://pypi.org/project/psycopg2/)
[![Scikit-learn](https://img.shields.io/badge/scikit_learn-1.1.2-3399cd)](https://scikit-learn.org/)
[![Xgboost](https://img.shields.io/badge/xgboost-1.6.2-189fdd)](https://xgboost.readthedocs.io/en/stable/)
[![Black](https://img.shields.io/badge/black-22.10.0-393a39)](https://black.readthedocs.io/en/stable/)
[![Isort](https://img.shields.io/badge/isort-5.10.1-ef8336)](https://isort.readthedocs.io/en/latest/)
[![Localstack](https://img.shields.io/badge/localstack-1.2.0-2d255e)](https://localstack.cloud/)
[![Pre-commit](https://img.shields.io/badge/pre_commit-2.20.0-f8b425)](https://pre-commit.com/)
[![Pylint](https://img.shields.io/badge/pylint-2.15.4-2a5adf)](https://pylint.pycqa.org/en/latest/)
[![Pytest](https://img.shields.io/badge/pytest-7.1.3-009fe2)](https://docs.pytest.org/en/7.2.x/)
<br><br><br>

In this MLOps project, we predict waiter tips based on features named _total bill, gender, smoker, day, time, and size_. We first deploy resources on _AWS_ with _Terraform_. Once we have all the data, the model, and scripts on the local machine and have completed the tests, we commit the project directory onto _GitHub_, which, through _Actions_, installs the files on Ubuntu virtual machine.

Later, we initiate the _MLflow_ and _Airflow_ servers to track experiments and manage the workflow. _Airflow_ automatically runs every month, checking if any new data exists in the _S3_ bucket and retrieving it from there to train a new model. The application saves the latest model in the _S3_ bucket to use in the production environment. We can watch all metrics by _Evidently_ on the localhost and by _Prometheus_ on the _Grafana_ dashboard. Every time we train the model and check for any data and concept drift, the user also receives an email notification.

<p align="center"> 
<img src="https://github.com/hsaltan/Machine-Learning/blob/main/Waiter-Tips-Prediction/images/wtp-diagram.png" />
</p>

Users can access the application through a web interface on _Flask_.

We run the tests on the local machine by implementing _pytest, black, isort, localstack, pre-commit,_ and _pylint_ before committing to _GitHub_.
<br>

## Installation

1. Create an AWS account and get a programmatic access.

2. Deploy AWS resources with _Terraform_. Run in the terraform folder:

```
terraform init
terraform plan
terraform apply -auto-approve
```

3. Commit the project to _GitHub_:

```
git add .
git commit -m 'initial commit'
git push origin main
```

If Actions are not in place, you can use `wget` command.

4. Install _brew_, _Prometheus_, start _Prometheus_ and _Grafana_ servers, and create _PostgreSQL_ databases on _RDS_ running the following command in the project folder:

```
start.sh
```
<br>

## Run

1. Start the MLflow server:

```
mlflow server -h 0.0.0.0 -p 5000 --backend-store-uri postgresql://DB_USER:DB_PASSWORD@DB_ENDPOINT:5432/DB_NAME --default-artifact-root s3://s3b-tip-predictor/mlflow/
```

2. Start the Evidently server:

```
mlflow server -h 0.0.0.0 -p 5500 --backend-store-uri postgresql://DB_USER:DB_PASSWORD@DB_ENDPOINT:5432/DB_NAME --default-artifact-root s3://s3b-tip-predictor/evidently/
```

You need to choose the database user and password, and get the RDS database endpoint.

3. Open the `airflow.cfg` and set executor as `LocalExecutor`, and `sql_alchemy_conn` as `sql_alchemy_conn = postgresql+psycopg2://<user>:<pass>@<host>:5432/<db>`

4. Initialize _Airflow_ database in the project folder (`/app/Waiter-Tips-Prediction`).

```
airflow db init
```

5. Create a user:

```
airflow users create --username <username> --password <password> --firstname <firstname> --lastname <lastname> --role Admin --email <email>
```

6. Start the _Airflow_ server:

```
airflow webserver -p 8080 -D
```

7. Start the _Airflow_ scheduler:

```
airflow scheduler -D
```

8. Do port forwarding on VSC for the following ports to access the Web UIs on the local machine:

* 3000: _Grafana_<br>
* 3500: _Flask_<br>
* 3600: _Flask_<br>
* 5000: _Mflow_<br>
* 5500: _Evidently_<br>
* 8080: _Airflow_ web server<br>
* 8793: _Airflow_ scheduler<br>
* 9090: _Prometheus_<br>
* 9091: _Prometheus_<br>

The _App_ (prediction) runs on port 3500, _Evidently_ reports on 3600, the app's _Prometheus_ metrics on 9091.

To start _MLflow_ and _Airflow_ servers readily, you can use `Makefile` provided that MLflow server endpoints are updated:

```
make mlflow_5000
make mlflow_5500
make airflow_web
make airflow_scheduler
```
c
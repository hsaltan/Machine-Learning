#! Use 'make' command at the beginning.
# Mlflow server at port 5000 for recording the results of the ML model
mlflow_5000:
	mlflow server -h 0.0.0.0 -p 5000 --backend-store-uri postgresql://postgres:password@mlflow-database.cmpdlb9srhwd.eu-west-1.rds.amazonaws.com:5432/mlflow_db --default-artifact-root s3://s3b-tip-predictor/mlflow/

# Mlflow server at port 5500 for recording the results of data drift by Evidently
mlflow_5500:
	mlflow server -h 0.0.0.0 -p 5500 --backend-store-uri postgresql://postgres:password@mlflow-database.cmpdlb9srhwd.eu-west-1.rds.amazonaws.com:5432/evidently --default-artifact-root s3://s3b-tip-predictor/evidently/

path:
	export AIRFLOW_HOME=/home/ubuntu/Waiter-Tips-Prediction

# First, type: export AIRFLOW_HOME=/Users/hasanserdaraltan/Downloads/waiter_tips_prediction
# Then, start airflow web server
airflow_web:
	airflow db init
	airflow webserver -p 8080 -D
	lsof -i tcp:8080

# If starting airflow server fails, run this
airflow_web_reset:
	rm airflow-webserver.err  airflow-webserver-monitor.pid

# Start airflow scheduler
airflow_scheduler:
	airflow scheduler -D
	lsof -i tcp:8793

# If starting airflow scheduler fails, run this
airflow_scheduler_reset:
	rm airflow-scheduler.err  airflow-scheduler.pid

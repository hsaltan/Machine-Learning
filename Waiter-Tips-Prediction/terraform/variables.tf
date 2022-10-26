variable "bucket" {
  type        = string
  description = "Bucket name"
  default     = "s3b-tip-predictor"
}

variable "sns_endpoint" {
  type        = string
  description = "Receiver email endpoint"
  default     = "serdarsbox-1@yahoo.com"
}

variable "artifact_paths" {
  type        = string
  description = "Artifact paths dictionary, e.g. {'mlflow_model_artifacts_path': str,  'evidently_artifacts_path': str}"
  default     = "{'mlflow_model_artifacts_path': 'models_mlflow',  'evidently_artifacts_path': 'evidently_metrics'}"
}

variable "inital_paths" {
  type        = string
  description = "Initial paths dictionary, e.g. {'mlflow_model_initial_path': str, 'evidently_initial_path': str}"
  default     = "{'mlflow_model_initial_path': 's3://s3b-tip-predictor/mlflow/', 'evidently_initial_path': 's3://s3b-tip-predictor/evidently/'}"
}

variable "tracking_server_host" {
  type        = string
  description = "Tracking server host address, e.g. 127.0.0.1"
  default     = "127.0.0.1"
}

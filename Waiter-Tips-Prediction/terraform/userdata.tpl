#!/bin/bash
sudo apt update -y
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install python3.9 -y
sudo apt install awscli -y
mkdir Waiter-Tips-Prediction
aws s3 cp s3://s3b-tip-predictor/config/requirements.txt .
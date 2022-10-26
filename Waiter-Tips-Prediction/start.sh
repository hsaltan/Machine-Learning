#!/bin/bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo '# Set PATH, MANPATH, etc., for Homebrew.' >> /home/ubuntu/.profile
echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> /home/ubuntu/.profile
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
sudo apt-get install build-essential
brew install gcc
brew install prometheus
brew services restart prometheus
cp -f /home/ubuntu/Waiter-Tips-Prediction/prometheus-config.yml /home/linuxbrew/.linuxbrew/etc/prometheus.yml
brew services restart prometheus
brew services info prometheus
sleep 5
sudo systemctl status postgresql.service --no-pager
sleep 5
sudo systemctl status grafana-server --no-pager
sleep 5
sudo pip install chardet==4.0.0
sudo pip install requests -U
sudo pip install -U click
sudo pip uninstall Flask-WTF -y
sudo pip uninstall  WTForms -y
sudo pip install Flask-WTF==0.15.1
sudo pip install  WTForms==2.3.3
echo 'export AIRFLOW_HOME=/home/ubuntu/Waiter-Tips-Prediction'
sudo airflow db init
sudo airflow users create --username serdar --password pass123 --firstname serdar --lastname altan --role Admin --email admin@example.com
sudo -i -u postgres
psql \
   --host=mlflow-database.cmpdlb9srhwd.eu-west-1.rds.amazonaws.com  \
   --port=5432 \
   --username=postgres \
   --password \
   --dbname=mlflow_db <<EOF
CREATE DATABASE mlflow;
CREATE DATABASE airflow;
CREATE DATABASE evidentlyy;
\l
EOF
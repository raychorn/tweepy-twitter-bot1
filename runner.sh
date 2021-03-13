#!/bin/bash

basedir=/tweepy-twitter-bot1
venv=$(ls $basedir/.venv*/bin/activate)
lib=$(ls $basedir/.venv*/lib/python3.9/site-packages)
echo "venv=$venv"
echo "lib=$lib"
export PYTHONPATH=$basedir/lib3/vyperlogix39.zip:$lib

. $venv
pip --version
pip install -r requirements.txt

#apt remove ca-certificates
#apt install ca-certificates -y

update-ca-certificates --fresh
export SSL_CERT_DIR=/etc/ssl/certs

python $basedir/tweepy-bot1.py "production"

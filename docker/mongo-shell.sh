#!/bin/bash

HOSTNAME=$(cat /proc/sys/kernel/hostname)

dir0=".."
dir1=".."

if [ "$HOSTNAME" != "DESKTOP-JJ95ENL" ]
then
    echo "Running via host-name $HOSTNAME and this seems to be Production."
    dir0="/workspaces"
    dir1="$dir0/tweepy-twitter-bot1"
fi

if [ -f $dir1/.env ]
then
    basedir=".."
    venv=$(ls $basedir/.venv*/bin/activate)
    echo "venv=$venv"
    if [ -f $venv ]
    then
        . $venv
        #python ./scripts/get_env.py
        export $(python ./scripts/get_env.py | sed 's/#.*//g' | xargs)
    fi
    #export $(cat $dir1/.env | sed 's/#.*//g' | xargs)
fi

CMD="mongo --username $MONGO_INITDB_ROOT_USERNAME --password --authenticationDatabase $MONGO_INITDB_DATABASE --host $MONGO_HOST --port $MONGO_PORT"
echo $CMD
$CMD

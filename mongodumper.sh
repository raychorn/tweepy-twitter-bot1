#!/bin/bash

export $(xargs < .env)

mongodump --host $MONGO_HOST --port $MONGO_PORT --username $MONGO_INITDB_ROOT_USERNAME --password $MONGO_INITDB_ROOT_PASSWORD --db $mongo_db_name --out ./mongo_$mongo_db_name/

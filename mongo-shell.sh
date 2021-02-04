#!/bin/bash

export $(xargs < .env)

mongo --username $MONGO_INITDB_ROOT_USERNAME --password --authenticationDatabase $MONGO_INITDB_DATABASE --host $MONGO_HOST --port $MONGO_PORT

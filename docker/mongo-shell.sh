#!/bin/bash

MONGO_INITDB_DATABASE=admin
echo $MONGO_INITDB_DATABASE
mongo --username root --password --authenticationDatabase $MONGO_INITDB_DATABASE --host 10.5.0.5 --port 27017

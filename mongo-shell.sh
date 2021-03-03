#!/bin/bash

export $(xargs < .env)

ARRAY=()
ARRAY+=("MONGO_HOST")
ARRAY+=("MONGO_CLUSTER")
ARRAY+=("COSMOSDB1")

PS3="Choose: "

select option in "${ARRAY[@]}";
do
    echo "Selected number: $REPLY"
    choice=${ARRAY[$REPLY-1]}
    break
done

if [[ $choice. == MONGO_HOST. ]]
then
    mongo --username $MONGO_INITDB_ROOT_USERNAME --password --authenticationDatabase $MONGO_INITDB_DATABASE --host $MONGO_HOST --port $MONGO_PORT
fi

if [[ $choice. == MONGO_CLUSTER. ]]
then
    mongo "mongodb+srv://cluster0.as9re.mongodb.net/admin" --username root
fi

if [[ $choice. == COSMOSDB1. ]]
then
    mongo $COSMOSDB1
fi


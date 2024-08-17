#!/bin/sh
cassandra -R

# Wait for Cassandra to start up
until cqlsh -e 'describe cluster' > /dev/null 2>&1; do
    echo "Waiting for Cassandra to start..."
    sleep 5
done

echo "Cassandra has started"

cqlsh --file '/code/scripts/create.cql'

echo "Cassandra has been initialised"

tail -f /dev/null
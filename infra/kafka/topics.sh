#!/bin/bash
# Create Kafka topics for PrimeEV factory streaming

kafka-topics --create --bootstrap-server kafka:29092 \
  --topic factory.sensors.raw \
  --partitions 15 \
  --replication-factor 1 \
  --if-not-exists

kafka-topics --create --bootstrap-server kafka:29092 \
  --topic factory.alerts.new \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

kafka-topics --create --bootstrap-server kafka:29092 \
  --topic factory.production.events \
  --partitions 5 \
  --replication-factor 1 \
  --if-not-exists

echo "Kafka topics created successfully."

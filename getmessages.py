from kafka import KafkaConsumer
import json

def consume_messages():
    # Create a Kafka consumer
    consumer = KafkaConsumer(
        'properties',  # Topic name
        bootstrap_servers=['localhost:9092'],  # Kafka broker address
        auto_offset_reset='earliest',  # Start reading at the earliest message
        enable_auto_commit=True,  # Automatically commit offsets
        group_id='my-group',  # Consumer group ID
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))  # Deserialize JSON messages
    )

    # # Seek to the beginning of each partition
    # for partition in consumer.partitions_for_topic('properties'):
    #     consumer.seek_to_beginning(partition)

    # Consume messages
    for message in consumer:
        print(f"Received message: {message.value}")

if __name__ == "__main__":
    consume_messages()
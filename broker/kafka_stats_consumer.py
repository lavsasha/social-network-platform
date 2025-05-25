import json
from datetime import datetime
from confluent_kafka import Consumer, KafkaException, KafkaError
from sqlalchemy.orm import sessionmaker
import time
import uuid
from statistic_service.db.clickhouse_models import Event, EventType


class KafkaStatsConsumer:
    def __init__(self, db):
        self.db = db
        self.consumer = Consumer({
            'bootstrap.servers': 'kafka:9092',
            'group.id': 'statistics_consumer_group',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False,
            'max.poll.interval.ms': 86400000
        })
        self.topic_map = {
            'post_views': EventType.VIEW,
            'post_likes': EventType.LIKE,
            'post_comments': EventType.COMMENT
        }
        self.max_retries = 10
        self.retry_delay = 10

    def wait_for_kafka(self):
        """Wait for Kafka to be ready and topics to be available."""
        retries = 0
        while retries < self.max_retries:
            try:
                metadata = self.consumer.list_topics(timeout=10)
                available_topics = set(metadata.topics.keys())
                required_topics = set(self.topic_map.keys())

                if not required_topics - available_topics:
                    return True

                time.sleep(self.retry_delay)
                retries += 1
            except Exception:
                time.sleep(self.retry_delay)
                retries += 1

        raise Exception(f"Failed to connect to Kafka after {self.max_retries} retries")

    def consume_messages(self):
        """Main message processing loop."""
        try:
            self.wait_for_kafka()
            self.consumer.subscribe(list(self.topic_map.keys()))

            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    self._handle_kafka_error(msg.error())
                    continue
                self._process_message(msg)
        finally:
            self._shutdown()

    def _handle_kafka_error(self, error: KafkaError):
        """Handle Kafka-specific errors."""
        if error.code() == KafkaError._PARTITION_EOF:
            return
        elif error.code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
            time.sleep(self.retry_delay)
        else:
            raise KafkaException(error)

    def _process_message(self, msg):
        """Process a single Kafka message and store it in the database."""
        Session = sessionmaker(bind=self.db.engine)
        session = Session()

        try:
            message = json.loads(msg.value())

            event = Event(
                event_id=str(uuid.uuid4()),
                post_id=message['post_id'],
                event_type=self.topic_map[msg.topic()],
                event_date=datetime.now().date()
            )

            session.add(event)
            session.commit()
            self.consumer.commit(asynchronous=False)
        except json.JSONDecodeError:
            session.rollback()
        except KeyError:
            session.rollback()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _shutdown(self):
        """Clean up the consumer on shutdown."""
        self.consumer.close()

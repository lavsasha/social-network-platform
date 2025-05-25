import json
from datetime import datetime
from confluent_kafka import Consumer, KafkaException, KafkaError
from sqlalchemy.orm import sessionmaker
import logging
import time
import uuid
from typing import Dict, Any
from statistic_service.db.clickhouse_models import Event, EventType


class KafkaStatsConsumer:
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger('KafkaConsumer')
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
        """Ожидает готовности Kafka и доступности топиков"""
        retries = 0
        while retries < self.max_retries:
            try:
                metadata = self.consumer.list_topics(timeout=10)
                available_topics = set(metadata.topics.keys())
                required_topics = set(self.topic_map.keys())
                if available_topics and (required_topics - available_topics):
                    self.logger.warning(
                        f"Some topics missing: {required_topics - available_topics}. "
                        f"Will try to continue with available topics."
                    )
                    return True

                if available_topics:
                    return True

                self.logger.warning(
                    f"Waiting for Kafka topics. "
                    f"Retry {retries + 1}/{self.max_retries}"
                )
            except Exception as e:
                self.logger.warning(
                    f"Kafka not ready yet: {str(e)}. "
                    f"Retry {retries + 1}/{self.max_retries}"
                )

            time.sleep(self.retry_delay)
            retries += 1

        raise Exception(f"Failed to connect to Kafka after {self.max_retries} retries")

    def consume_messages(self):
        """Основной цикл обработки сообщений"""
        try:
            self.wait_for_kafka()

            self.consumer.subscribe(list(self.topic_map.keys()))
            self.logger.info(f"Subscribed to topics: {list(self.topic_map.keys())}")

            while True:
                msg = self.consumer.poll(1.0)

                if msg is None:
                    continue

                if msg.error():
                    self.handle_kafka_error(msg.error())
                    continue

                self.process_message_safely(msg)

        except Exception as e:
            self.logger.error(f"Fatal error in consumer: {str(e)}", exc_info=True)
        finally:
            self.shutdown()

    def handle_kafka_error(self, error: KafkaError):
        """Обрабатывает ошибки Kafka"""
        if error.code() == KafkaError._PARTITION_EOF:
            return
        elif error.code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
            self.logger.error(f"Topic not found, will retry: {error.str()}")
            time.sleep(self.retry_delay)
        else:
            self.logger.error(f"Kafka error: {error.str()}")

    def process_message_safely(self, msg):
        """Безопасная обработка сообщения с транзакцией"""
        Session = sessionmaker(bind=self.db.engine)
        session = None

        try:
            message = json.loads(msg.value())
            self.logger.debug(f"Processing message from {msg.topic()}: {message}")

            session = Session()

            event = Event(
                event_id=str(uuid.uuid4()),
                post_id=message['post_id'],
                event_type=self.topic_map[msg.topic()],
                event_date=datetime.now().date()
            )

            session.add(event)
            session.commit()
            self.consumer.commit(asynchronous=False)

            self.logger.info(
                f"Successfully processed {event.event_type} event "
                f"for post {event.post_id}"
            )

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse message: {msg.value()}. Error: {str(e)}")
        except KeyError as e:
            self.logger.error(f"Missing required field in message: {str(e)}")
            if session:
                session.rollback()
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}", exc_info=True)
            if session:
                session.rollback()
        finally:
            if session:
                session.close()

    def shutdown(self):
        """Корректное завершение работы consumer"""
        try:
            self.consumer.close()
            self.logger.info("Kafka consumer stopped gracefully")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from confluent_kafka import Producer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")


class KafkaProducer:
    def __init__(self):
        self.producer = Producer({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'client.id': 'social_network_producer'
        })

        self.USER_REGISTRATIONS_TOPIC = "user_registrations"
        self.POST_VIEWS_TOPIC = "post_views"
        self.POST_LIKES_TOPIC = "post_likes"
        self.POST_COMMENTS_TOPIC = "post_comments"

    def _delivery_report(self, err, msg):
        """Called once for each message produced to indicate delivery result."""
        if err is not None:
            print(f'Message delivery failed: {err}')
        else:
            print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    def _serialize_datetime(self, obj):
        """JSON serializer for datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def send_event(self, topic: str, data: Dict[str, Any], key: Optional[str] = None):
        """Send an event to the specified Kafka topic."""
        payload = json.dumps(data, default=self._serialize_datetime).encode('utf-8')
        self.producer.produce(
            topic=topic,
            key=key.encode('utf-8') if key else None,
            value=payload,
            callback=self._delivery_report
        )
        self.producer.flush()

    def send_user_registration_event(self, user_id: str, email: str, registration_date: datetime):
        """Send event when a user registers."""
        self.send_event(
            topic=self.USER_REGISTRATIONS_TOPIC,
            data={
                "event_type": "user_registration",
                "user_id": user_id,
                "email": email,
                "registration_date": registration_date
            },
            key=str(user_id)
        )

    def send_post_viewed_event(self, user_id: str, post_id: str):
        """Send event when a post is viewed."""
        self.send_event(
            topic=self.POST_VIEWS_TOPIC,
            data={
                "event_type": "post_viewed",
                "timestamp": datetime.now(),
                "user_id": user_id,
                "post_id": post_id
            },
            key=str(post_id)
        )

    def send_post_liked_event(self, user_id: str, post_id: str):
        """Send event when a post is liked."""
        self.send_event(
            topic=self.POST_LIKES_TOPIC,
            data={
                "event_type": "post_liked",
                "timestamp": datetime.now(),
                "user_id": user_id,
                "post_id": post_id
            },
            key=str(post_id)
        )

    def send_post_commented_event(self, user_id: str, post_id: str, comment_id: str, text: str = None):
        """Send event when a post is commented."""
        event_data = {
            "event_type": "post_commented",
            "timestamp": datetime.now(),
            "user_id": user_id,
            "post_id": post_id,
            "comment_id": comment_id
        }
        if text:
            event_data["text_preview"] = text[:100]
        self.send_event(
            topic=self.POST_COMMENTS_TOPIC,
            data=event_data,
            key=str(post_id))


kafka_producer = KafkaProducer()

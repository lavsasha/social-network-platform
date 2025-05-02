import pytest
import json
from confluent_kafka import Consumer, KafkaException
import time
from datetime import datetime
import requests


@pytest.fixture(scope="module")
def kafka_consumer():
    conf = {
        'bootstrap.servers': 'kafka:9092',
        'group.id': 'test-group',
        'auto.offset.reset': 'earliest',
        'session.timeout.ms': 6000,
        'enable.auto.commit': False
    }
    consumer = Consumer(conf)
    yield consumer
    consumer.close()


@pytest.fixture(scope="module")
def test_user():
    return {
        "login": "kafka_test_user",
        "password": "KafkaTest123!",
        "email": "kafka.test@example.com",
        "first_name": "Kafka",
        "last_name": "Test"
    }


def test_user_registration_event(kafka_consumer, test_user):
    kafka_consumer.subscribe(['user_registrations'])
    response = requests.post(
        'http://api_gateway:8080/api/v1/register',
        json=test_user
    )
    assert response.status_code == 201

    start_time = time.time()
    while time.time() - start_time < 10:
        msg = kafka_consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            raise KafkaException(msg.error())

        event = json.loads(msg.value())
        if event.get("email") == test_user["email"]:
            assert event['event_type'] == 'user_registration'
            assert 'user_id' in event
            assert event['email'] == test_user["email"]
            assert 'registration_date' in event
            return

    pytest.fail("Event not received in Kafka within timeout")


def test_post_view_event(kafka_consumer, test_user):
    login_response = requests.post(
        'http://api_gateway:8080/api/v1/login',
        json={
            "login": test_user["login"],
            "password": test_user["password"]
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    post_response = requests.post(
        'http://api_gateway:8080/api/v1/posts',
        headers={"Authorization": token},
        json={
            "title": "Kafka Test Post",
            "description": "Post for Kafka testing",
            "is_private": False
        }
    )
    assert post_response.status_code == 201
    post_id = post_response.json()["post_id"]
    kafka_consumer.subscribe(['post_views'])
    view_response = requests.post(
        f'http://api_gateway:8080/api/v1/posts/{post_id}/view',
        headers={"Authorization": token}
    )
    assert view_response.status_code == 200

    start_time = time.time()
    while time.time() - start_time < 10:
        msg = kafka_consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            raise KafkaException(msg.error())

        event = json.loads(msg.value())
        if event.get("post_id") == str(post_id):
            assert event['event_type'] == 'post_viewed'
            assert 'user_id' in event
            assert 'post_id' in event
            assert datetime.fromisoformat(event['timestamp']).tzinfo is None
            assert msg.key() == str(post_id).encode('utf-8')
            return

    pytest.fail("Event not received in Kafka within timeout")


def test_post_like_event(kafka_consumer, test_user):
    login_response = requests.post(
        'http://api_gateway:8080/api/v1/login',
        json={
            "login": test_user["login"],
            "password": test_user["password"]
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    post_response = requests.post(
        'http://api_gateway:8080/api/v1/posts',
        headers={"Authorization": token},
        json={
            "title": "Kafka Like Test",
            "description": "Post for like testing",
            "is_private": False
        }
    )
    assert post_response.status_code == 201
    post_id = post_response.json()["post_id"]
    kafka_consumer.subscribe(['post_likes'])
    like_response = requests.post(
        f'http://api_gateway:8080/api/v1/posts/{post_id}/like',
        headers={"Authorization": token}
    )
    assert like_response.status_code == 200

    start_time = time.time()
    while time.time() - start_time < 10:
        msg = kafka_consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            raise KafkaException(msg.error())

        event = json.loads(msg.value())
        if event.get("post_id") == str(post_id):
            assert event['event_type'] == 'post_liked'
            assert 'user_id' in event
            assert 'post_id' in event
            assert datetime.fromisoformat(event['timestamp']).tzinfo is None
            assert msg.key() == str(post_id).encode('utf-8')
            return

    pytest.fail("Event not received in Kafka within timeout")


def test_post_comment_event(kafka_consumer, test_user):
    login_response = requests.post(
        'http://api_gateway:8080/api/v1/login',
        json={
            "login": test_user["login"],
            "password": test_user["password"]
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    post_response = requests.post(
        'http://api_gateway:8080/api/v1/posts',
        headers={"Authorization": token},
        json={
            "title": "Kafka Comment Test",
            "description": "Post for comment testing",
            "is_private": False
        }
    )
    assert post_response.status_code == 201
    post_id = post_response.json()["post_id"]

    kafka_consumer.subscribe(['post_comments'])
    comment_text = "Test comment for Kafka"
    comment_response = requests.post(
        f'http://api_gateway:8080/api/v1/posts/{post_id}/comment',
        headers={"Authorization": token},
        json={"text": comment_text}
    )
    assert comment_response.status_code == 201
    comment_id = comment_response.json()["comment_id"]

    start_time = time.time()
    while time.time() - start_time < 10:
        msg = kafka_consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            raise KafkaException(msg.error())

        event = json.loads(msg.value())
        if event.get("post_id") == str(post_id) and event.get("comment_id") == str(comment_id):
            assert event['event_type'] == 'post_commented'
            assert 'user_id' in event
            assert 'post_id' in event
            assert 'comment_id' in event
            assert datetime.fromisoformat(event['timestamp']).tzinfo is None
            assert msg.key() == str(post_id).encode('utf-8')
            assert event.get("text_preview") == comment_text[:100]
            return

    pytest.fail("Event not received in Kafka within timeout")

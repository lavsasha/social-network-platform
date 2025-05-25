import grpc
from concurrent import futures
import threading
import time
import signal
from db.statistic_db import StatisticDB
from api.statistic_grpc_service import StatisticServiceServicer
from proto import statistic_pb2_grpc
from broker.kafka_stats_consumer import KafkaStatsConsumer


def serve():
    stop_event = threading.Event()

    def shutdown(signum, frame):
        print("\nShutdown signal received")
        stop_event.set()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        db = StatisticDB('clickhouse://default:password@clickhouse:8123/default')
        print("Database connected")

        consumer = KafkaStatsConsumer(db)
        consumer_thread = threading.Thread(target=consumer.consume_messages)
        consumer_thread.daemon = True
        consumer_thread.start()
        print("Kafka consumer started")

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        statistic_pb2_grpc.add_StatisticServiceServicer_to_server(
            StatisticServiceServicer(db), server)

        server.add_insecure_port('[::]:50052')
        server.start()
        print("gRPC server started on port 50052")

        while not stop_event.is_set():
            if not consumer_thread.is_alive():
                print("Error: Kafka consumer thread stopped!")
                break
            time.sleep(1)

    except Exception as e:
        print(f"Critical error: {str(e)}")
        raise
    finally:
        print("Shutting down services...")
        if 'consumer' in locals():
            consumer.shutdown()
        if 'server' in locals():
            server.stop(0)
        if 'db' in locals():
            db.close()
        print("Service stopped")


if __name__ == '__main__':
    serve()

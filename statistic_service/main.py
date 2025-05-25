import grpc
from concurrent import futures
import threading
import time
import logging
import signal
from db.statistic_db import StatisticDB
from api.statistic_grpc_service import StatisticServiceServicer
from proto import statistic_pb2_grpc
from broker.kafka_stats_consumer import KafkaStatsConsumer


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def serve():
    configure_logging()
    logger = logging.getLogger('StatisticService')
    stop_event = threading.Event()

    def shutdown(signum, frame):
        logger.info("Received shutdown signal")
        stop_event.set()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        db = StatisticDB('clickhouse://default:password@clickhouse:8123/default')
        logger.info("Database connection established")

        consumer = KafkaStatsConsumer(db)
        consumer_thread = threading.Thread(target=consumer.consume_messages)
        consumer_thread.daemon = True
        consumer_thread.start()
        logger.info("Kafka consumer started")

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        statistic_pb2_grpc.add_StatisticServiceServicer_to_server(
            StatisticServiceServicer(db), server)

        server.add_insecure_port('[::]:50052')
        server.start()
        logger.info("gRPC server started on port 50052")

        while not stop_event.is_set():
            if not consumer_thread.is_alive():
                logger.error("Kafka consumer thread died!")
                break
            time.sleep(1)

    except Exception as e:
        logger.error(f"Service failed: {str(e)}", exc_info=True)
        raise
    finally:
        logger.info("Shutting down services...")
        if 'consumer' in locals():
            consumer.shutdown()
        if 'server' in locals():
            server.stop(0)
        if 'db' in locals():
            db.close()
        logger.info("Service stopped")


if __name__ == '__main__':
    serve()

from concurrent import futures
import time
import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from proto import post_pb2_grpc
from proto.post_pb2_grpc import add_PostServiceServicer_to_server
from api.post_grpc_service import PostServiceServicer
from db.post_db import PostDB
import sys
import os
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def serve():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('PostService')
    server = None
    try:
        db = PostDB(os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/post_db"))
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_PostServiceServicer_to_server(PostServiceServicer(db), server)
        health_servicer = health.HealthServicer()
        health_servicer.set('', health_pb2.HealthCheckResponse.SERVING)
        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
        server.add_insecure_port('[::]:50051')
        server.start()
        logger.info("Server started on port 50051")
        while True:
            time.sleep(60)

    except Exception as e:
        logger.error(f"Server failed: {str(e)}", exc_info=True)
        raise

    finally:
        if server:
            server.stop(0)
        db.close()


if __name__ == '__main__':
    serve()

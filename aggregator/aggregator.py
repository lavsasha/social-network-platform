import time
import logging
from datetime import datetime, timedelta
import grpc
from concurrent.futures import ThreadPoolExecutor
from proto import statistic_pb2, statistic_pb2_grpc, post_pb2, post_pb2_grpc

AGGREGATION_INTERVAL_MINUTES = 15
MAX_WORKERS = 5
SYSTEM_USER_ID = "aggregator"
STATISTIC_SERVICE_URL = "statistic_service:50052"
POST_SERVICE_URL = "post_service:50051"


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def get_statistic_stub():
    channel = grpc.insecure_channel(STATISTIC_SERVICE_URL)
    return statistic_pb2_grpc.StatisticServiceStub(channel)


def get_post_stub():
    channel = grpc.insecure_channel(POST_SERVICE_URL)
    return post_pb2_grpc.PostServiceStub(channel)


def get_post_creator_id(post_id: str) -> str:
    try:
        stub = get_post_stub()
        response = stub.GetPost(
            post_pb2.GetPostRequest(post_id=post_id, user_id=SYSTEM_USER_ID)
        )
        return response.post.creator_id
    except grpc.RpcError as e:
        logging.error(f"Failed to get creator for post {post_id}: {e.details()}")
        raise


def process_post(post_id, stats_stub):
    try:
        creator_id = get_post_creator_id(post_id)
        stats_stub.GetPostStats(
            statistic_pb2.PostStatsRequest(post_id=post_id, user_id=creator_id)
        )
        logging.info(f"Processed post {post_id} for user {creator_id}")
        return True
    except Exception as e:
        logging.error(f"Error processing post {post_id}: {str(e)}")
        return False


def run_aggregation():
    logging.info("Starting aggregation...")
    start_time = datetime.now()

    try:
        stats_stub = get_statistic_stub()
        post_ids_response = stats_stub.GetPostIds(statistic_pb2.GetPostIdsRequest())
        post_ids = post_ids_response.post_ids

        if not post_ids:
            logging.warning("No posts found for aggregation")
            return

        logging.info(f"Found {len(post_ids)} posts to process")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(process_post, post_id, stats_stub)
                for post_id in post_ids
            ]
            success_count = sum(1 for f in futures if f.result())
            error_count = len(futures) - success_count

        duration = datetime.now() - start_time
        logging.info(
            f"Aggregation completed. Success: {success_count}, "
            f"Errors: {error_count}, Duration: {duration.total_seconds():.2f} sec"
        )

    except Exception as e:
        logging.error(f"Aggregation failed: {str(e)}")
        raise


def wait_for_service(service_name: str, url: str, timeout_seconds: int = 5, retry_delay: int = 5):
    while True:
        try:
            channel = grpc.insecure_channel(url)
            grpc.channel_ready_future(channel).result(timeout=timeout_seconds)
            logging.info(f"{service_name} is ready!")
            channel.close()
            break
        except grpc.FutureTimeoutError:
            logging.warning(f"{service_name} not ready, retrying in {retry_delay} sec...")
            time.sleep(retry_delay)
        except Exception as e:
            logging.error(f"Unexpected error checking {service_name}: {str(e)}")
            time.sleep(retry_delay)


def main():
    configure_logging()

    wait_for_service(
        service_name="Statistic Service",
        url=STATISTIC_SERVICE_URL
    )
    wait_for_service(
        service_name="Post Service",
        url=POST_SERVICE_URL
    )

    logging.info(f"Aggregator service started (interval: every {AGGREGATION_INTERVAL_MINUTES} minutes)")
    run_aggregation()

    while True:
        next_run = datetime.now() + timedelta(minutes=AGGREGATION_INTERVAL_MINUTES)
        logging.info(f"Next aggregation at {next_run}")
        time.sleep(AGGREGATION_INTERVAL_MINUTES * 60)
        run_aggregation()


if __name__ == '__main__':
    main()

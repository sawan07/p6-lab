"""Settings come only from environment variables (Cloud report, Appendix B: no keys or
passwords in the image). Names follow the report's Appendix B where they apply."""
import os

QUEUE_NAME = os.environ.get("SQS_INGRESS_QUEUE_NAME", "ingress-transactions.fifo")
REDIS_URL = os.environ.get("REDIS_CLUSTER_READ_ENDPOINT", "redis://redis:6379/0")
REPLICA_DSN = os.environ.get("DB_READ_REPLICA_DSN", "")
PRIMARY_DSN = os.environ.get("DB_PRIMARY_DSN", "")
AWS = dict(endpoint_url=os.environ.get("AWS_ENDPOINT_URL", "http://localstack:4566"),
           region_name=os.environ.get("AWS_DEFAULT_REGION", "eu-west-2"))


def ingress_queue(sqs):
    """Create the FIFO queue if it does not exist yet (idempotent) and return its URL."""
    return sqs.create_queue(QueueName=QUEUE_NAME, Attributes={"FifoQueue": "true"})["QueueUrl"]

"""Database worker: drains the SQS FIFO queue and applies the writes to the primary
database, so a burst from one interface cannot exhaust the database (report 3.1.1)."""
import json
import time

import boto3
import psycopg

from common import AWS, PRIMARY_DSN, ingress_queue

sqs = boto3.client("sqs", **AWS)
while True:
    try:
        QUEUE_URL = ingress_queue(sqs)
        break
    except Exception:
        time.sleep(2)
print("worker: draining", QUEUE_URL, flush=True)
while True:
    try:
        msgs = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=10, WaitTimeSeconds=5).get("Messages", [])
        if msgs:
            with psycopg.connect(PRIMARY_DSN) as db:
                for m in msgs:
                    p = json.loads(m["Body"])
                    db.execute("INSERT INTO transactions (transaction_id, ui_id, user_id, operation, payload_hash) "
                               "VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                               (p["transactionId"], p["originatingUiId"], p["payloadData"]["userId"],
                                p["payloadData"]["operationType"], p["payloadHash"]))
                    sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=m["ReceiptHandle"])
            print(f"worker: applied {len(msgs)} write(s)", flush=True)
    except Exception as exc:  # queue or database not ready yet
        print("worker: waiting -", type(exc).__name__, flush=True)
        time.sleep(3)

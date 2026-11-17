"""Write path (Cloud report 3.1.1, FR-1): validate every payload against the declarative
schema, then push it to an SQS FIFO queue instead of writing to the database directly.
Bursts wait in the queue; the database worker drains it at its own pace."""
import json
import pathlib

import boto3
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from jsonschema import Draft202012Validator, FormatChecker

from common import AWS, ingress_queue

SCHEMA = json.loads((pathlib.Path(__file__).parent / "ingress-transaction-payload.schema.json").read_text())
validator = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
sqs = boto3.client("sqs", **AWS)
QUEUE_URL = ingress_queue(sqs)
app = FastAPI(title="write-service")


@app.post("/write/transactions")
async def accept(request: Request):
    payload = await request.json()
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if errors:  # rejected before it can reach the queue or the database
        return JSONResponse(status_code=400, content={
            "status": "rejected", "correlationId": request.headers.get("x-correlation-id"),
            "errors": [f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in errors]})
    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(payload),
                     MessageGroupId=payload["originatingUiId"],
                     MessageDeduplicationId=payload["payloadData"]["idempotencyKey"])
    return JSONResponse(status_code=202, content={
        "status": "queued", "queue": QUEUE_URL.rsplit("/", 1)[-1],
        "transactionId": payload["transactionId"], "correlationId": request.headers.get("x-correlation-id")})

"""Read path (Cloud report 3.1.2, FR-1 / NFR-3): reads come from Redis, falling back to a
read replica. READ_THROUGH_CACHE switches between the two configurations in load-test
runs 02 and 03 (report 3.2.1):
  false -> every search goes to the replica (the cache-miss wave of run 02)
  true  -> read-through caching: a miss loads the row and stores it in Redis (the fix)"""
import json
import os

import redis
from fastapi import FastAPI, HTTPException
from psycopg_pool import ConnectionPool

from common import REDIS_URL, REPLICA_DSN

READ_THROUGH = os.environ.get("READ_THROUGH_CACHE", "true").lower() == "true"
POOL = int(os.environ.get("REPLICA_POOL_SIZE", "4"))
cache = redis.Redis.from_url(REDIS_URL)
pool = ConnectionPool(REPLICA_DSN, min_size=1, max_size=POOL, timeout=5, open=True)
app = FastAPI(title="read-service")


@app.get("/read/profiles/{profile_id}")
def profile(profile_id: int):
    key = f"profile:{profile_id}"
    if READ_THROUGH and (hit := cache.get(key)):
        return {**json.loads(hit), "source": "cache"}
    with pool.connection() as db:  # the replica query (deliberately costly, like a search)
        row = db.execute("SELECT id, ui_id, display_name, pg_sleep(0.03) IS NULL FROM profiles WHERE id = %s",
                         (profile_id,)).fetchone()
    if not row:
        raise HTTPException(404, "profile not found")
    data = {"id": row[0], "uiId": row[1], "displayName": row[2]}
    if READ_THROUGH:
        cache.set(key, json.dumps(data), ex=300)
    return {**data, "source": "read-replica"}


@app.get("/read/config")
def config():
    return {"readThroughCache": READ_THROUGH, "replicaPoolSize": POOL}

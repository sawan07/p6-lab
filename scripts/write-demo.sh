#!/bin/sh
# Write path demo (report 3.1.1, FR-1, FR-2): a valid payload is queued, an invalid one is
# rejected by the schema, and a burst from one interface is rate limited at the edge.
URL=http://localhost:8087/write/transactions
valid() { cat <<J
{"transactionId":"$(python3 -c 'import uuid;print(uuid.uuid4())')","originatingUiId":"${2:-UI_02}","timestamp":$(date +%s)000,
 "payloadHash":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
 "payloadData":{"userId":"usr_992348512","operationType":"WRITE_MUTATION","idempotencyKey":"idem_$(python3 -c 'import uuid;print(uuid.uuid4().hex[:12])')_$1"}}
J
}
echo "1. Valid payload from UI_02:"
valid 1 | curl -s -H "Content-Type: application/json" -H "X-Client-UI: UI_02" -d @- $URL; echo
echo
echo "2. Invalid payload (unknown UI, text timestamp, missing idempotencyKey):"
curl -s -H "Content-Type: application/json" -H "X-Client-UI: UI_09" $URL -d \
 '{"transactionId":"not-a-uuid","originatingUiId":"UI_09","timestamp":"yesterday","payloadHash":"x","payloadData":{"userId":"u1","operationType":"WRITE_MUTATION"}}'; echo
echo
echo "3. Burst: 60 writes at once from UI_02 (limit 20/s, burst 10), then 5 from UI_04:"
for i in $(seq 1 60); do valid "b$i" | curl -s -o /dev/null -w "%{http_code}\n" -H "Content-Type: application/json" -H "X-Client-UI: UI_02" -d @- $URL & done | sort | uniq -c | sed 's/^/   UI_02: /'
wait
for i in $(seq 1 5); do valid "c$i" UI_04 | curl -s -o /dev/null -w "%{http_code}\n" -H "Content-Type: application/json" -H "X-Client-UI: UI_04" -d @- $URL; done | sort | uniq -c | sed 's/^/   UI_04: /'
sleep 10
echo
echo "4. Applied to the primary database by the worker:"
docker compose exec -T db-primary psql -U platform -d platform -tAc \
  "SELECT ui_id || ': ' || count(*) || ' transaction(s)' FROM transactions GROUP BY ui_id ORDER BY ui_id" | sed 's/^/   /'

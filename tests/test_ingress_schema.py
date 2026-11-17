"""Contract checks for the write path (Cloud report 3.1.1). The valid payload is the one in
the report's Appendix A."""
import copy
import json
import pathlib

import pytest
from jsonschema import Draft202012Validator, FormatChecker

SCHEMA = json.loads((pathlib.Path(__file__).parents[1] / "services/ingress-transaction-payload.schema.json").read_text())
V = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
APPENDIX_A = {
    "transactionId": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6", "originatingUiId": "UI_02", "timestamp": 1780957121000,
    "payloadHash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "payloadData": {"userId": "usr_992348512", "operationType": "WRITE_MUTATION", "idempotencyKey": "idem_key_sec2_run_03_p95"},
}


def test_appendix_a_payload_is_valid():
    assert not list(V.iter_errors(APPENDIX_A))


@pytest.mark.parametrize("path,value", [
    (("originatingUiId",), "UI_06"),                 # only five client interfaces exist
    (("timestamp",), "1780957121000"),               # epoch millis must be an integer
    (("transactionId",), "not-a-uuid"),              # correlation ID must be a UUID
    (("payloadData", "operationType"), "DELETE_ALL"),
])
def test_invalid_values_are_rejected(path, value):
    p = copy.deepcopy(APPENDIX_A)
    target = p
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert list(V.iter_errors(p))


def test_missing_idempotency_key_is_rejected():
    p = copy.deepcopy(APPENDIX_A)
    del p["payloadData"]["idempotencyKey"]
    assert list(V.iter_errors(p))

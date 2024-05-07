from __future__ import annotations

import pymongo
import pytest

MONGODB_HOST = "127.0.0.1"
MONGODB_PORT = 27017
MONGODB_TEST_DBNAME = "telethon_test_mongodb_sessions"
MONGODB_TEST_COLL = "telegram"


@pytest.fixture(autouse=True, scope="session")
def _up_mongodb():
    """Up mongodb test database."""
    client = pymongo.MongoClient(host=MONGODB_HOST, port=MONGODB_PORT)
    db = client[MONGODB_TEST_DBNAME]
    db[MONGODB_TEST_COLL]

    yield

    client.drop_database(MONGODB_TEST_DBNAME)
    client.close()

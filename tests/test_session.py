"""File contain tests for `telethon_multimongo_session.MongoSession`."""

import pymongo
import pytest
import telethon as th
from telethon_multimongo_session import MongoSession

from tests.conftest import (
    MONGODB_HOST,
    MONGODB_PORT,
    MONGODB_TEST_COLL,
    MONGODB_TEST_DBNAME,
)

# This api credentails use arch linux developers for build telegram desktop.
API_ID = 611335
API_HASH = "d524b414d21f4d37f08684c1df41ac9c"
# Phone number for connect to telegram test servers.
PHONE_NUMBER = "9996621234"
# Code wich test account will be recieved
CODE = PHONE_NUMBER[5] * 5


TELEGRAM_DATA_CENTERS_IP = {"2": "149.154.167.40"}


@pytest.fixture()
def telethon() -> th.TelegramClient:
    """Fixture for `telethon.TelegramClient`."""
    session = MongoSession(
        api_id=API_ID,
        api_hash=API_HASH,
        phone=PHONE_NUMBER,
        database=MONGODB_TEST_DBNAME,
        coll=MONGODB_TEST_COLL,
        host=MONGODB_HOST,
        port=MONGODB_PORT,
    )
    client = th.TelegramClient(session, api_id=API_ID, api_hash=API_HASH)
    # Set dc for test servers
    dc_id = int(PHONE_NUMBER[5])
    # Get dc ip
    ip = TELEGRAM_DATA_CENTERS_IP[dc_id]
    # Set dc in session
    client.session.set_dc(dc_id, ip, 80)
    return client


@pytest.mark.asyncio()
async def test_session(telethon: th.TelegramClient) -> None:
    """Test func for `MongoSession`."""
    # Connect to telegram and write some data to session
    await telethon.start(phone=PHONE_NUMBER, code_callback=lambda: CODE)
    me = await telethon.get_me()
    assert me
    # Disconnect
    await telethon.disconnect()

    # Assert that some data stored in mongodb
    mongodb = pymongo.MongoClient(host=MONGODB_HOST, port=MONGODB_PORT)
    coll = mongodb[MONGODB_TEST_DBNAME][MONGODB_TEST_COLL]

    assert coll.find_one(telethon.session.session_filter)

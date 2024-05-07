"""Telethon multi-mongodb session.

Session stored in mongodb and may be use for store multiple sessions of
`telethon.TelegramClient` client.
"""

from __future__ import annotations

from telethon_multimongo_session.mongo_session import (
    MemorySession,
    MongoSession,
)

__all__ = ["MongoSession", "MemorySession"]
__version__ = "0.0.1"

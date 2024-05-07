"""Telethon Session which stored in MongoDB."""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any, Dict, Self, TypeVar

from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.collection import Collection
from telethon.sessions import MemorySession
from telethon.types import updates
from typing_extensions import override

if TYPE_CHECKING:
    from telethon import tl

T = TypeVar("T")


class Entity(BaseModel):
    """Telegram entity."""

    id: int
    hash: int
    username: str | None
    phone: str | None
    name: str | None


class Session(BaseModel):
    """Session entity."""

    dc_id: int | None
    server_address: str | None
    port: int | None
    auth_key: bytes | None
    takeout_id: int | None


class SentFile(BaseModel):
    """Sent file telegram entity."""

    id: int
    md5_digest: bytes | None
    file_size: int | None
    type: int | None
    hash: int | None


class UpdateState(BaseModel):
    """Telegram update state entity."""

    id: int
    pts: int | None
    qts: int | None
    date: int | None
    seq: int | None


class Version(BaseModel):
    """Version."""

    version: int | None


CURRENT_VERSION = 1


class MongoSession(MemorySession):
    """Store for sessions of `TelegramClient's` in MongoDB.

    Parameters
    ----------
    api_id : int
        Telegram API ID
    api_hash : str
        Telegram API Hash
    phone : str
        Telegram phone
    database : str
        Database name
    host : str
        MongoDB host
    port : int
        MongoDB port
    coll : str or Collection
        Collection name or instance of `pymongo.Collection`
    *args: Any
        Additional arguments which passed to `pymongo.MongoClient`
    **kwargs: Any
        Additional keyword arguments which passed to `pymongo.MongoClient`

    """

    def __init__(
        self,
        api_id: int | str,
        api_hash: str,
        phone: str,
        database: str,
        host: str = "127.0.0.1",
        port: int = 27017,
        coll: str | Collection | None = None,
        *mongo_args,
        **mongo_kwargs,
    ) -> None:
        super().__init__()
        self._filter = {"api_id": api_id, "api_hash": api_hash, "phone": phone}
        self._client = MongoClient(
            host=host, port=port, *mongo_args, **mongo_kwargs
        )
        self._db = self._client[database]
        if isinstance(coll, str):
            self._coll = self._db[coll]
        elif isinstance(coll, Collection):
            self._coll = coll
        elif not coll:
            self._coll = self._db["telegram"]
        else:
            msg = "`coll` arg must be str or Collection"
            raise ValueError(msg)

        self._api_id = api_id
        self._api_hash = api_hash

        self.logger = logging.getLogger(__name__)
        self.save_entities = True
        self._prepare_database()

    @property
    def session_filter(self) -> Dict:
        """dict: Session filter (unique id).

        Used to filter session in `MongoSession`.

        Examples
        --------
        >>> session_filter = session.session_filter
        >>> session_filter
        {'api_id': 12345, 'api_hash': 'hash', 'phone': '+9996627985'}
        """
        return self._filter

    def _prepare_database(self):
        data = self._coll.find_one(filter=self._filter)

        if data is None:
            data = {
                "sessions": [],
                "sent_files": [],
                "update_states": [],
                "entities": [],
                "versions": [Version(version=CURRENT_VERSION).model_dump()],
            }

        elif data.get("versions"):
            data["versions"] = [Version(version=CURRENT_VERSION).model_dump()]

        if (
            isinstance(data, dict)
            and isinstance(data.get("sessions"), list)
            and data["sessions"]
        ):
            from telethon.crypto import AuthKey

            session = Session(**data["sessions"][0])
            self._dc_id = session.dc_id
            self._server_address = session.server_address
            self._port = session.port
            self._takeout_id = session.takeout_id
            self._auth_key = AuthKey(data=session.auth_key)

            if len(data["sessions"]) > 0:
                del data["sessions"][1:]

        self._coll.update_one(self._filter, update={"$set": data}, upsert=True)

    @override
    def clone(self, to_instance: T | None = None) -> T | Self:
        cloned = super().clone(to_instance=to_instance)
        cloned.save_entites = self.save_entites
        return cloned

    @override
    def _upgrade_database(self, *args):
        pass

    @override
    def set_dc(self, dc_id: int, server_address: str, port: int) -> None:
        super().set_dc(dc_id, server_address, port)
        self._update_session_table()

    @MemorySession.auth_key.setter
    def auth_key(self, value: str) -> None:
        """str: Telegram auth key."""
        self._auth_key = value
        self._update_session_table()

    @MemorySession.takeout_id.setter
    def takeout_id(self, value: Any) -> None:
        """Set takeout id in MongoDB."""
        self._takeout_id = value
        self._update_session_table()

    def _update_session_table(self):
        session = Session(
            dc_id=self._dc_id,
            server_address=self._server_address,
            port=self._port,
            auth_key=self._auth_key.key if self._auth_key else b"",
            takeout_id=self._takeout_id,
        )

        data = self._coll.find_one(filter=self._filter)
        key = "sessions"

        if data.get(key) is None:
            data[key] = []

        data[key] = [session.model_dump()]

        update = {"$set": {key: data[key]}}
        mongo_filter = self._filter
        return self._coll.update_one(
            filter=mongo_filter, update=update, upsert=True
        )

    @override
    def get_update_state(self, entity_id: int) -> None | updates.State:
        data = self._coll.find_one(filter=self._filter)
        if data.get("update_states") is None:
            return None

        row = next(
            (
                update_state
                for update_state in data["update_states"]
                if update_state["id"] == entity_id
            ),
            None,
        )
        if row:
            row = UpdateState(**row)
            row.date = datetime.datetime.fromtimestamp(
                row.date, tz=datetime.timezone.utc
            )
            return updates.State(
                row.pts, row.qts, row.date, row.seq, unread_count=0
            )
        return None

    @override
    def set_update_state(self, entity_id: int, state: UpdateState) -> None:
        super().set_update_state(entity_id=entity_id, state=state)
        update_state = UpdateState(
            id=entity_id,
            pts=state.pts,
            qts=state.qts,
            date=state.date.timestamp(),
            seq=state.seq,
        )

        data = self._coll.find_one(filter=self._filter)
        if update_state.id in [
            update_state_["id"] for update_state_ in data["update_states"]
        ]:
            return None

        key = "update_states"

        if data.get(key) is None:
            data[key] = []

        data[key].append(update_state.model_dump())

        update = {"$set": {key: data[key]}}
        mongo_filter = self._filter
        return self._coll.update_one(
            filter=mongo_filter, update=update, upsert=True
        )

    @override
    def delete(self) -> None:
        key = "sessions"
        data = self._coll.find_one(self._filter)

        if not data or not data.get(key):
            return

        data[key] = []
        self._coll.update_one(self._filter, {"$set": {key: data[key]}})

    @override
    def process_entities(self, tlo: tl.TLObject) -> None:
        if not self.save_entities:
            return

        super().process_entities(tlo=tlo)

        rows = self._entities_to_rows(tlo)
        if not rows:
            return
        data = self._coll.find_one(self._filter)

        entities = data.get("entities") or []
        for row in rows:
            if row[0] in [entity["id"] for entity in data["entities"]]:
                continue

            entity = Entity(
                id=row[0],
                hash=row[1],
                username=row[2],
                phone=row[3],
                name=row[4],
            )
            entities.append(entity.model_dump())

        mongo_filter = self._filter
        update = {"$set": {"entities": entities}}
        self._coll.update_one(filter=mongo_filter, update=update, upsert=True)

    @override
    def get_entity_rows_by_phone(self, phone: str) -> None | tuple[int, str]:
        obj = self._coll.find_one(self._filter)
        for entity in obj["entities"]:
            if str(entity.get("phone")) == str(phone):
                return (entity["id"], entity["hash"])
        return None

    @override
    def get_entity_rows_by_username(
        self, username: str
    ) -> None | tuple[int, str]:
        obj = self._coll.find_one(self._filter)
        for entity in obj["entities"]:
            if entity.get("username") == username:
                return (entity["id"], entity["hash"])
        return None

    @override
    def get_entity_rows_by_name(self, name: str) -> None:
        obj = self._coll.find_one(self._filter)
        for entity in obj["entities"]:
            if entity.get("name") == name:
                return (entity["id"], entity["hash"])
        return None

    @override
    def get_entity_rows_by_id(
        self, entity_id: int, exact: bool = True
    ) -> None | tuple[int, str]:
        from telethon import utils
        from telethon.types import PeerChannel, PeerChat, PeerUser

        ids = (
            utils.get_peer_id(PeerUser(entity_id)),
            utils.get_peer_id(PeerChat(entity_id)),
            utils.get_peer_id(PeerChannel(entity_id)),
        )

        obj = self._coll.find_one(self._filter)
        for entity in obj["entities"]:
            if (
                exact
                and entity.get("id") == entity_id
                or not exact
                and entity["id"] in ids
            ):
                return (entity["id"], entity["hash"])
        return None

    @override
    def get_file(
        self, md5_digest: Any, file_size: Any, cls: type
    ) -> None | tuple[int, str]:
        from telethon.sessions.memory import _SentFileType

        data = self._coll.find_one(filter=self._filter)
        for sent_file in data["sent_files"]:
            if sent_file.get("md5_digest") != md5_digest:
                continue

            if sent_file.get("file_size") != file_size:
                continue

            if sent_file.get("type") == _SentFileType.from_type(cls).value:
                return cls(sent_file["id"], sent_file["hash"])
        return None

    @override
    def cache_file(
        self, md5_digest: Any, file_size: Any, instance: object
    ) -> None:
        from telethon.sessions.memory import _SentFileType
        from telethon.types import InputDocument, InputPhoto

        if not isinstance(instance, (InputDocument, InputPhoto)):
            msg = f"Cannot cache {type(instance)} instance"
            raise TypeError(msg)

        data = self._coll.find_one(self._filter)
        if instance.id in [
            cache_file["id"] for cache_file in data["sent_files"]
        ]:
            return

        super().cache_file(
            md5_digest=md5_digest, file_size=file_size, instance=instance
        )

        sent_file = SentFile(
            id=instance.id,
            md5_digest=md5_digest,
            file_size=file_size,
            type=_SentFileType.from_type(type(instance)).value,
            hash=instance.access_hash,
        )

        key = "sent_files"

        if data.get(key) is None:
            data[key] = []

        data[key].append(sent_file.model_dump())

        update = {"$set": {key: data[key]}}

        self._coll.update_one(
            filter=self._filter,
            update=update,
        )

    def from_session(
        self,
        session: MemorySession,
        set_auth_key: bool = False,
        set_update_states: bool = False,
    ) -> None:
        """
        Save data from Any Session Classes (which bases on `MemorySession`).

        Parameters
        ----------
        session: MemorySession
            Any session which based on `MemorySession`.
        set_auth_key: bool, optional
            Whether the auth key needs to be set in session, default by False.
        set_updates_stat: bool, optional
            Whether the update states needs to be set in session,
            default by False.
        """
        if set_auth_key:
            self._auth_key = session._auth_key

        self._entities = session._entities
        self.set_dc(
            dc_id=session._dc_id,
            server_address=session._server_address,
            port=session._port,
        )

        if set_update_states:
            for entity_id, update_state in session.get_update_states():
                self.set_update_state(entity_id, update_state)

# mautrix-signal - A Matrix-Signal puppeting bridge
# Copyright (C) 2020 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from typing import Optional, ClassVar, List, Union, TYPE_CHECKING
from uuid import UUID

from attr import dataclass
import asyncpg

from mautrix.types import RoomID
from mautrix.util.async_db import Database

fake_db = Database("") if TYPE_CHECKING else None


@dataclass
class Portal:
    db: ClassVar[Database] = fake_db

    chat_id: Union[UUID, str]
    receiver: str
    mxid: Optional[RoomID]
    name: Optional[str]
    encrypted: bool

    async def insert(self) -> None:
        q = ("INSERT INTO portal (chat_id, receiver, mxid, name, encrypted) "
             "VALUES ($1, $2, $3, $4, $5)")
        await self.db.execute(q, self.chat_id, self.receiver, self.mxid, self.name, self.encrypted)

    async def update(self) -> None:
        q = ("UPDATE portal SET mxid=$3, name=$4, encrypted=$5 "
             "WHERE chat_id=$1::text AND receiver=$2")
        await self.db.execute(q, self.chat_id, self.receiver, self.mxid, self.name, self.encrypted)

    @classmethod
    def _from_row(cls, row: asyncpg.Record) -> 'Portal':
        data = {**row}
        if data["receiver"]:
            chat_id = UUID(data.pop("chat_id"))
        else:
            chat_id = data.pop("chat_id")
        return cls(chat_id=chat_id, **data)

    @classmethod
    async def get_by_mxid(cls, mxid: RoomID) -> Optional['Portal']:
        q = "SELECT chat_id, receiver, mxid, name, encrypted FROM portal WHERE mxid=$1"
        row = await cls.db.fetchrow(q, mxid)
        if not row:
            return None
        return cls._from_row(row)

    @classmethod
    async def get_by_chat_id(cls, chat_id: Union[UUID, str], receiver: str = ""
                             ) -> Optional['Portal']:
        q = ("SELECT chat_id, receiver, mxid, name, encrypted "
             "FROM portal WHERE chat_id=$1::text AND receiver=$2")
        row = await cls.db.fetchrow(q, chat_id, receiver)
        if not row:
            return None
        return cls._from_row(row)

    @classmethod
    async def find_private_chats_of(cls, receiver: str) -> List['Portal']:
        q = "SELECT chat_id, receiver, mxid, name, encrypted FROM portal WHERE receiver=$1"
        rows = await cls.db.fetch(q, receiver)
        return [cls._from_row(row) for row in rows]

    @classmethod
    async def find_private_chats_with(cls, other_user: UUID) -> List['Portal']:
        q = ("SELECT chat_id, receiver, mxid, name, encrypted FROM portal "
             "WHERE chat_id=$1::text AND receiver<>''")
        rows = await cls.db.fetch(q, other_user)
        return [cls._from_row(row) for row in rows]

    @classmethod
    async def all_with_room(cls) -> List['Portal']:
        q = "SELECT chat_id, receiver, mxid, name, encrypted FROM portal WHERE mxid IS NOT NULL"
        rows = await cls.db.fetch(q)
        return [cls._from_row(row) for row in rows]
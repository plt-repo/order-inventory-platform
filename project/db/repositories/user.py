from typing import Type

from project.db.models.users import User
from project.db.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    @property
    def model(self) -> Type[User]:
        return User

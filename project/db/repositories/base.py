from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple, Type, TypeVar, Union

from sqlalchemy import Column, delete, func
from sqlalchemy import update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList

from project.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(ABC):
    """
    Abstract Base Class for data repositories.

    This class provides a standard interface for common database operations
    (CRUD - Create, Read, Update, Delete) using SQLAlchemy's async features.
    It is designed to be inherited by specific repositories for each model.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initializes the BaseRepository.

        :param session: The SQLAlchemy AsyncSession instance to use for database operations.
        """
        self.session = session

    @property
    @abstractmethod
    def model(self) -> Type[ModelType]:
        """ORM Model."""
        raise NotImplementedError

    def _select(self) -> Select[Tuple[ModelType]]:
        """Getting a SELECT query for a related model without a filter."""
        return select(self.model)

    def _get_attr(self, attr: str):
        """
        Getting a model attribute by name.

        :param attr:
        :return:
        """
        return getattr(self.model, attr)

    def _where_condition(
        self,
        **kwargs: Any,
    ) -> Union[BinaryExpression, BooleanClauseList, None]:
        """Getting conditions for the WHERE method based on specified fields."""
        condition = None
        for attr, value in kwargs.items():
            if "__lte" in attr:
                attr = attr.replace("__lte", "")
                expression = self._get_attr(attr) <= value
            elif "__gte" in attr:
                attr = attr.replace("__gte", "")
                expression = self._get_attr(attr) >= value
            elif "__in" in attr:
                attr = attr.replace("__in", "")
                expression = self._get_attr(attr).in_(value)
            else:
                expression = self._get_attr(attr) == value
            if condition is not None:
                condition &= expression
            else:
                condition = expression
        return condition

    def _select_where(self, **kwargs: Any) -> Select:
        """Getting a SELECT query with WHERE filtering."""
        query = self._select()
        condition = self._where_condition(**kwargs)
        if condition is not None:
            query = query.where(condition)
        return query

    async def find_one_by(self, **kwargs: Any) -> Optional[ModelType]:
        """
        Search for one object by specified filters.

        :param kwargs:
        :return:
        """
        cursor = await self.session.execute(self._select_where(**kwargs))
        return cursor.scalar_one_or_none()

    async def find_all_by(
            self,
            offset: int | None = None,
            limit: int | None = None,
            load_related_names: list[str] = None,
            where_related: dict[str, dict] = None,
            unique=False,
            **kwargs: Any,
    ) -> List[ModelType]:
        if not load_related_names:
            load_related_names = []
        if not where_related:
            where_related = {}

        query = self._select_where(**kwargs)

        for rel_name, filters in where_related.items():
            related_model = getattr(self.model, rel_name).property.mapper.class_
            query = query.join(related_model)
            for field, value in filters.items():
                query = query.where(getattr(related_model, field) == value)

        for related_name in load_related_names:
            query = query.options(joinedload(self._get_attr(related_name)))

        query = query.order_by(self.model.id)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        cursor = await self.session.execute(query)
        if unique:
            return cursor.unique().scalars().all()
        else:
            return cursor.scalars().all()

    async def find_first(self, **kwargs) -> ModelType | None:
        cursor = await self.session.execute(self._select_where(**kwargs))
        return cursor.scalars().first()

    async def update_many(self, filter_dict: dict, update: dict, commit: bool = True) -> int:
        condition = self._where_condition(**filter_dict)
        if condition is None:
            return 0

        stmt = sql_update(self.model).where(condition).values(**update)
        result = await self.session.execute(stmt)

        if commit:
            await self.session.commit()

        return result.rowcount

    async def update_one(
        self,
        filter_dict: dict,
        update: dict,
        skip_locked: bool = False,
    ) -> Optional[ModelType]:
        query = (
            self._select_where(**filter_dict)
            .with_for_update(skip_locked=skip_locked)
            .limit(1)
        )
        cursor = await self.session.execute(query)
        instance = cursor.scalars().first()

        if not instance:
            return None

        for key, value in update.items():
            setattr(instance, key, value)

        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def get_or_create(self, lookup: dict, defaults: dict):
        result = await self.session.execute(self._select_where(**lookup))
        instance = result.scalar_one_or_none()
        if instance:
            return False, instance
        params = {**lookup, **defaults}
        return True, await self.create(**params)

    async def update_or_create(self, lookup: dict, defaults: dict) -> Tuple[bool, ModelType]:
        result = await self.session.execute(self._select_where(**lookup))
        instance = result.scalar_one_or_none()
        if instance:
            for key, value in defaults.items():
                setattr(instance, key, value)
            await self.session.commit()
            await self.session.refresh(instance)
            created = False
        else:
            params = {**lookup, **defaults}
            instance = self.model(**params)
            self.session.add(instance)
            await self.session.commit()
            await self.session.refresh(instance)
            created = True

        return created, instance

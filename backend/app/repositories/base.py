from typing import Any, Generic, Optional, TypeVar

from sqlalchemy.orm import Session

from app.db.session import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: Any) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def list(
        self,
        page: int = 1,
        limit: int = 20,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        desc: bool = True,
    ) -> tuple[list[ModelType], int]:
        query = self.db.query(self.model)
        if filters:
            for field, value in filters.items():
                column = getattr(self.model, field, None)
                if column is not None and value:
                    query = query.filter(column == value)
        total = query.count()
        if order_by:
            column = getattr(self.model, order_by, None)
            if column is not None:
                query = query.order_by(column.desc() if desc else column.asc())
        items = query.offset((page - 1) * limit).limit(limit).all()
        return items, total

    def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(self, id: Any, **kwargs) -> Optional[ModelType]:
        instance = self.get(id)
        if not instance:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, id: Any) -> bool:
        instance = self.get(id)
        if not instance:
            return False
        self.db.delete(instance)
        self.db.commit()
        return True

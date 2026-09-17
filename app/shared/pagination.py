"""Bentuk paginasi yang dipakai seluruh modul.

Supaya semua endpoint daftar punya bentuk response yang sama, dan
frontend tidak perlu menangani tiga bentuk berbeda.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        if self.size == 0:
            return 0
        return -(-self.total // self.size)

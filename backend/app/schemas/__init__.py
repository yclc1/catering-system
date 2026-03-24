"""Common schemas."""
from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")


class PageRequest(BaseModel):
    page: int = 1
    page_size: int = 20
    keyword: Optional[str] = None


class PageResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    message: str


class DropdownItem(BaseModel):
    id: int
    name: str
    code: Optional[str] = None

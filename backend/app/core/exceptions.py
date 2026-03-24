"""Custom exceptions."""
from fastapi import HTTPException, status


class MonthClosedError(HTTPException):
    def __init__(self, month: str):
        super().__init__(
            status_code=status.HTTP_423_LOCKED,
            detail=f"月份 {month} 已结账锁定，无法修改"
        )


class NotFoundError(HTTPException):
    def __init__(self, resource: str, id: int = None):
        detail = f"{resource} 不存在"
        if id:
            detail = f"{resource} (ID: {id}) 不存在"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class DuplicateError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class BusinessError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

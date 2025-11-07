from typing import TypeVar
from fastapi_pagination import Page as BasePage
from fastapi_pagination.customization import (
    CustomizedPage,
    UseName,
    UseParamsFields
)


# Default Page arguments used for paginated returns
T = TypeVar('T')
Page = CustomizedPage[
    BasePage[T],
    UseName('Page'),
    UseParamsFields(size=50),
]

from fastapi_pagination import Page as BasePage
from fastapi_pagination.customization import (
    CustomizedPage,
    UseName,
    UseParamsFields
)


# Default Page arguments used for paginated returns
Page = CustomizedPage[
    BasePage,
    UseName('Page'),
    UseParamsFields(size=50),
]

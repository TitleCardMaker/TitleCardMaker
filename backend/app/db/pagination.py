from fastapi_pagination import Page
from fastapi_pagination.customization import (
    CustomizedPage,
    UseName,
    UseParamsFields
)


# Default Page arguments used for paginated returns
Page = CustomizedPage[
    Page,
    UseName('Page'),
    UseParamsFields(size=50),
]

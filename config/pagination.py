from typing import Any

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        page = self.page

        assert page is not None, "paginate_queryset must be called first"
        assert self.request is not None, "request must be set"

        return Response(
            {
                "items": data,
                "meta": {
                    "page": page.number,
                    "page_size": self.get_page_size(self.request),
                    "total": page.paginator.count,
                    "total_pages": page.paginator.num_pages,
                    "has_next_page": page.has_next(),
                    "has_previous_page": page.has_previous(),
                },
            }
        )

    def get_paginated_response_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        """
        Định nghĩa schema cho drf-spectacular để sinh OpenAPI đúng format.
        Viết bằng snake_case, hook camelize_serializer_fields sẽ convert sang camelCase.
        """
        return {
            "type": "object",
            "required": ["items", "meta"],
            "properties": {
                "items": schema,
                "meta": {
                    "type": "object",
                    "required": [
                        "page",
                        "page_size",
                        "total",
                        "total_pages",
                        "has_next_page",
                        "has_previous_page",
                    ],
                    "properties": {
                        "page": {"type": "integer", "example": 1},
                        "page_size": {"type": "integer", "example": 20},
                        "total": {"type": "integer", "example": 100},
                        "total_pages": {"type": "integer", "example": 5},
                        "has_next_page": {"type": "boolean", "example": True},
                        "has_previous_page": {"type": "boolean", "example": False},
                    },
                },
            },
        }

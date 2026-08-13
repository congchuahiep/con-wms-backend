"""
Custom DRF exception handler.

Chuẩn hóa mọi error response về format thống nhất, tránh collision giữa
field errors và metadata keys (code, detail).

Output luôn có dạng:
    {
        "code": "error_code_string",       # DRF's default_code
        "detail": "human readable message", # DRF's default_detail hoặc detail từ exception
        "fields": {                         # Chỉ có khi là ValidationError
            "field_name": ["error messages"]
        }
    }
"""

from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    """
    Custom exception handler.

    Gọi DRF mặc định trước, sau đó chuẩn hóa response structure để:
    - Tách field-level errors vào key "fields" (tránh collision với code/detail)
    - Đảm bảo mọi response đều có "code" và "detail" ở top-level
    """
    response = drf_exception_handler(exc, context)

    if response is None:
        return None

    # Xác định code & detail từ exception
    if isinstance(exc, APIException):
        error_code = getattr(exc, "default_code", "error")

        # ValidationError với detail dạng dict → field-level errors
        if isinstance(exc, ValidationError) and isinstance(exc.detail, dict):
            field_errors = {}
            for key, value in exc.detail.items():
                if isinstance(value, list):
                    field_errors[key] = value
                elif isinstance(value, str):
                    field_errors[key] = [value]
                else:
                    field_errors[key] = [str(value)]

            response.data = {
                "code": error_code,
                "detail": exc.default_detail,
                "fields": field_errors,
            }
            return response

        # ValidationError với detail dạng list → non-field errors
        if isinstance(exc, ValidationError) and isinstance(exc.detail, list):
            detail_msg = "; ".join(str(e) for e in exc.detail)
            response.data = {
                "code": error_code,
                "detail": detail_msg,
            }
            return response

        # Các APIException khác (Auth, Permission, NotFound, …)
        detail_msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        response.data = {
            "code": error_code,
            "detail": detail_msg,
        }
        return response

    # Fallback cho các exception không phải APIException (vd: Http404, PermissionDenied)
    detail_text = ""
    if isinstance(response.data, dict):
        detail_text = response.data.get("detail", "")
    elif isinstance(response.data, str):
        detail_text = response.data
    elif isinstance(response.data, list):
        detail_text = str(response.data[0]) if response.data else ""

    response.data = {
        "code": "error",
        "detail": detail_text or str(exc),
    }

    # Cố gắng xác định status code chính xác hơn
    if response.status_code is None:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return response

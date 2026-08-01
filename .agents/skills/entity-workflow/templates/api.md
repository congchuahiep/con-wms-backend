# API Endpoints — {{ENTITY_NAME}}

## Danh sách endpoint

| Method | Endpoint | Mô tả | Request Body | Response |
|---|---|---|---|---|
| `GET` | `/api/{{prefix}}/` | Liệt kê | — | `[{...}]` |
| `POST` | `/api/{{prefix}}/` | Tạo mới | `{...}` | `{...}` |
| `GET` | `/api/{{prefix}}/{id}/` | Chi tiết | — | `{...}` |
| `PUT` | `/api/{{prefix}}/{id}/` | Cập nhật | `{...}` | `{...}` |
| `DELETE` | `/api/{{prefix}}/{id}/` | Xoá | — | `204 No Content` |

## Ghi chú

- Permission: `{{PERMISSION_CLASS}}`
- Filter: `{{FILTER_FIELDS}}`
- Search: `{{SEARCH_FIELDS}}`

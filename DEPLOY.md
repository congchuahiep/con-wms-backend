# DEPLOY — Backend (con-wms) lên Google Cloud Run

> Hướng dẫn đóng gói backend thành container và triển khai lên **Cloud Run**.
> Frontend (Vercel) + Database (Neon/Supabase) do bạn tự triển khai — chỉ cần cấp cho backend:
> - `DATABASE_URL` (PostgreSQL — xem §3)
> - URL Cloud Run thành phẩm → dán vào **Vercel** env `NEXT_PUBLIC_API_URL`

## 1. Yêu cầu

- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) đã đăng nhập: `gcloud auth login`
- Docker (chỉ cần cho build image)
- Đã có project GCP + bật billing (free tier Cloud Run vẫn dùng được)

```bash
export PROJECT=wms-project            # project GCP của bạn
export REGION=asia-southeast1         # Singapore — gần VN, ping thấp
export SERVICE=wms-backend
export IMAGE=$REGION-docker.pkg.dev/$PROJECT/wms/backend
```

## 2. Build & push image lên Artifact Registry

> ⚡ Nếu dùng GitHub Actions (workflow `.github/workflows/backend.yml`) thì **bỏ qua bước này** —
> job `deploy` dùng **source-based deploy** (`source: .`): Cloud Run tự build từ `Dockerfile` trong repo.

```bash
gcloud auth configure-docker $REGION-docker.pkg.dev
gcloud artifacts repositories create wms --repository-format=docker \
  --location=$REGION --description="WMS images"

docker build -t $IMAGE:latest .
docker push $IMAGE:latest
```

> Image tự chạy `collectstatic` (WhiteNoise phục vụ static/admin) và serve qua
> **Gunicorn** đúng `$PORT` mà Cloud Run cấp. Health check: `GET /healthz/`.

## 3. Tạo database (Neon/Supabase) + lưu secret

- Tạo PostgreSQL free tier trên **Neon** (0.5GB, tự ngủ) hoặc **Supabase** (500MB).
- Lấy connection string dạng: `postgresql://user:password@host/dbname?sslmode=require`
- Tạo secret trên GCP Secret Manager:

```bash
echo -n 'postgresql://user:password@host/dbname?sslmode=require' | \
  gcloud secrets create wms-database-url --data-file=-
echo -n 'MOT_SECRET_KEY_DAI_VA_NGẪU_NHIÊN_32+KÝ_TỰ' | \
  gcloud secrets create wms-secret-key --data-file=-
```

## 4. Deploy Cloud Run

```bash
gcloud run deploy $SERVICE \
  --image $IMAGE:latest \
  --region $REGION \
  --cpu 1 --memory 512Mi --min-instances 0 --max-instances 3 \
  --allow-unauthenticated \
  --set-env-vars DEBUG=False,ENABLE_DEMO_SEED=False \
  --set-env-vars ALLOWED_HOSTS=$(gcloud run services describe $SERVICE --region $REGION --format='value(status.url)' | sed 's|https://||') \
  --set-secrets SECRET_KEY=wms-secret-key:latest,DATABASE_URL=wms-database-url:latest
```

> - `--allow-unauthenticated`: Cloud Run URL công khai, nhưng **mọi API đều cần JWT**
>   (ngoại trừ login/register) nên an toàn như một endpoint nội bộ phía sau ứng dụng.
>   Muốn chặt hơn → đặt sau load balancer + IAM (xem §7).
> - `DEBUG=False` sẽ **từ chối khởi động** nếu thiếu `SECRET_KEY`/`ALLOWED_HOSTS` (bảo vệ ngược).
> - Dù deploy bằng `gcloud` hay GitHub Actions đều được — workflow tự động:
>   migrate → deploy (`source: .`) → smoke test `/healthz/`.

Lấy URL thành phẩm:

```bash
gcloud run services describe $SERVICE --region $REGION --format='value(status.url)'
# → https://wms-backend-xxxx-asia-southeast1.run.app
```

Dán URL này vào Vercel: `NEXT_PUBLIC_API_URL=https://...run.app` (+ `NEXT_PUBLIC_URL`, `NEXT_PUBLIC_GOOGLE_MAP_API`).

## 5. Chạy migration (một lần — Không bật sẵn trong entrypoint)

> ✅ Nếu dùng GitHub Actions: job `migrate` chạy **tự động trước job deploy** (trong runner,
> dùng `DATABASE_URL` secret). Chỉ làm thủ công khi cần migrate ngoài pipeline.

Cách A — Cloud Run Job (chuẩn):

```bash
gcloud run jobs create wms-backend-migrate \
  --image $IMAGE:latest --region $REGION --task-timeout 900s \
  --set-env-vars RUN_MIGRATIONS=1,DEBUG=False,ENABLE_DEMO_SEED=False \
  --set-env-vars ALLOWED_HOSTS=* \
  --set-secrets SECRET_KEY=wms-secret-key:latest,DATABASE_URL=wms-database-url:latest
gcloud run jobs execute wms-backend-migrate --region $REGION
```

Cách B — nhanh tại chỗ (chỉ khi có quyền truy cập DB):

```bash
docker build -t con-wms-backend:local .
docker run --rm -e RUN_MIGRATIONS=1 -e DATABASE_URL='postgresql://...' \
  -e SECRET_KEY=x -e DEBUG=False -e ALLOWED_HOSTS=* con-wms-backend:local
```

Kiểm tra nhanh dịch vụ: `curl https://<service>.run.app/healthz/` → `{"status": "ok"}`

## 6. Tạo tài khoản admin đầu tiên

Chạy một lần (Cloud Run Job replay cách §5-A với command khác):

```bash
gcloud run jobs create wms-admin-create --image $IMAGE --region $REGION \
  --command .venv/bin/python --args "manage.py,createsuperuser" \
  --set-env-vars DEBUG=False,ENABLE_DEMO_SEED=False \
  --set-secrets SECRET_KEY=...,DATABASE_URL=...
gcloud run jobs execute wms-admin-create --region $REGION
```

## 7. (Nâng cao) Muốn chặt hơn `--allow-unauthenticated`

Với app thật nên đặt:
- Load balancer (cloud Run + LB + IAM `run.invoker`) — đắt hơn chút, có WAF/CDN
- Hoặc ít nhất: `gcloud run services update --ingress internal-and-cloud-load-balancing`

## 8. Local dev vẫn như cũ

```bash
uv sync            # cài deps (có gunicorn/whitenoise/psycopg mới)
cp .env.example .env   # (nếu tạo) — DEBUG mặc định True, SQLite, seed bật
python manage.py runserver
```

> Tất cả config prod đọc từ env — không đổi code khi chuyển môi trường.
# HW4: Docker 微服務系統 — nginx + Node.js / Rust / Python + PostgreSQL

5 個容器的微服務：`nginx`（web server + reverse proxy + 前端展示頁）
+ `Node.js` + `Rust` + `Python` 三個後端 + `PostgreSQL` 資料庫。
已在本機驗證 `docker compose up` 全綠、`curl` 四路健康檢查皆通。

## 目錄結構（繳交內容：Dockerfile + docker-compose.yml）

```
HW4/
├── docker-compose.yml      # 編排 5 個服務
├── nginx/
│   ├── Dockerfile          # FROM nginx:1.27-alpine
│   ├── nginx.conf          # reverse proxy：/api/node|rust|python
│   └── html/index.html     # 簡易 Web 展示介面（老師開瀏覽器看這頁）
├── backend-node/
│   ├── Dockerfile          # FROM node:20-alpine
│   ├── package.json
│   └── server.js           # Express + pg
├── backend-rust/
│   ├── Dockerfile          # 多階段：rust:alpine 建置 → alpine:3.20 執行
│   ├── Cargo.toml
│   └── src/main.rs         # Axum + tokio-postgres
├── backend-python/
│   ├── Dockerfile          # FROM python:3.12-slim
│   ├── requirements.txt
│   └── app.py              # Flask + psycopg2
├── db/init.sql             # PostgreSQL 初始化（visits + system_info）
└── README.md               # 本文件
```

## 架構

```
Browser → http://localhost:8080
  ├─ /               → nginx 靜態前端（html/index.html）
  ├─ /health         → nginx 自檢
  ├─ /api/node/*    → api-node:3000   (Node.js 20 + Express)
  ├─ /api/rust/*    → api-rust:8000   (Rust + Axum)
  └─ /api/python/*  → api-python:5000 (Python 3.12 + Flask)
                        └─→ postgres:5432 (PostgreSQL 16, db: microdb)
```

每個後端統一 API：`GET /health`、`GET /info（含 DB 版本 + visits 筆數）`、`GET /visits`、`POST /visits`。
三種語言共用同一張 `visits` 表，前端按「+visit」可證明共用資料庫。

## 執行（老師 / 評分者操作）

```powershell
cd HW4
docker compose up --build -d
docker compose ps
```

開啟瀏覽器：**http://localhost:8080**，點各卡片「檢查」即可看到
三種語言後端即時回傳 + PostgreSQL 版本。含「一鍵全檢查」與 10 秒自動刷新。

## 驗證指令

```powershell
curl http://localhost:8080/health
curl http://localhost:8080/api/node/info
curl http://localhost:8080/api/rust/info
curl http://localhost:8080/api/python/info
docker compose logs -f nginx
docker compose down -v
```

## 對應題目要求

| 要求 | 實現 |
|---|---|
| nginx web server, reverse proxy | `nginx` 容器，`nginx.conf` 設 upstream + proxy_pass |
| postgresql 資料庫 | `postgres:16-alpine` + `db/init.sql` + volume `pgdata` + healthcheck |
| 開發執行環境 node.js, rust, python | 三個獨立 Dockerfile 微服務，各自 `EXPOSE` 對內 port |
| 簡易 web 介面展示 docker 系統 | `nginx/html/index.html` dashboard，即時 fetch 各服務 |
| Dockerfile 和 docker-compose.yml | 共 4 個 Dockerfile + 1 個 compose，`docker compose config` 已驗證 |

## 推上 GitHub（_se111410546 倉庫）

```powershell
# 假設已 clone：https://github.com/an-625/_se111410546.git
Copy-Item -Recurse -Force HW4 <repo>\HW4
cd <repo>
git add HW4
git commit -m "HW4: Docker 微服務系統"
git push origin main
```

use axum::{routing::{get, post}, Json, Router};
use serde_json::{json, Value};
use std::{env, time::{SystemTime, UNIX_EPOCH}};
use tower_http::cors::CorsLayer;

fn now_iso() -> String {
    let s = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
    format!("epoch:{s}")
}

fn db_url() -> String {
    env::var("DATABASE_URL").unwrap_or("postgres://micro:micro123@postgres:5432/microdb".into())
}

async fn query_db() -> Value {
    match tokio_postgres::connect(&db_url(), tokio_postgres::NoTls).await {
        Ok((client, connection)) => {
            tokio::spawn(async move { let _ = connection.await; });
            let ver: String = client.query_one("SELECT version()", &[]).await
                .map(|r| r.get(0)).unwrap_or("unknown".into());
            let count: i64 = client.query_one("SELECT COUNT(*) FROM visits", &[]).await
                .map(|r| r.get(0)).unwrap_or(-1);
            json!({"connected": true, "postgres_version": ver, "visits_count": count})
        }
        Err(e) => json!({"connected": false, "error": e.to_string()}),
    }
}

async fn health() -> Json<Value> {
    Json(json!({"status":"ok","service":"api-rust","language":"Rust + Axum","timestamp": now_iso()}))
}

async fn info() -> Json<Value> {
    let hostname = hostname::get_hostname();
    Json(json!({
        "service":"api-rust","language":"Rust","framework":"Axum",
        "rust_version": rustc_version::version(),
        "hostname": hostname, "db": query_db().await, "timestamp": now_iso()
    }))
}

async fn visits() -> Json<Value> {
    match tokio_postgres::connect(&db_url(), tokio_postgres::NoTls).await {
        Ok((client, connection)) => {
            tokio::spawn(async move { let _ = connection.await; });
            match client.query("SELECT id, service, created_at::text FROM visits ORDER BY id DESC LIMIT 10", &[]).await {
                Ok(rows) => {
                    let list: Vec<Value> = rows.iter().map(|r| {
                        let id: i32 = r.get(0); let svc: String = r.get(1); let ts: String = r.get(2);
                        json!({"id": id, "service": svc, "created_at": ts})
                    }).collect();
                    Json(json!({"service":"api-rust","rows": list}))
                }
                Err(e) => Json(json!({"error": e.to_string()})),
            }
        }
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn add_visit() -> Json<Value> {
    match tokio_postgres::connect(&db_url(), tokio_postgres::NoTls).await {
        Ok((client, connection)) => {
            tokio::spawn(async move { let _ = connection.await; });
            match client.query_one("INSERT INTO visits(service) VALUES('rust') RETURNING id, service, created_at::text", &[]).await {
                Ok(r) => {
                    let id: i32 = r.get(0); let svc: String = r.get(1); let ts: String = r.get(2);
                    Json(json!({"inserted": {"id": id, "service": svc, "created_at": ts}}))
                }
                Err(e) => Json(json!({"error": e.to_string()})),
            }
        }
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

// tiny helpers to avoid extra crates
mod hostname {
    pub fn get_hostname() -> String {
        std::env::var("HOSTNAME").unwrap_or_else(|_| "micro-rust".into())
    }
}
mod rustc_version {
    pub fn version() -> String {
        "stable (Axum 0.7)".to_string()
    }
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/", get(health))
        .route("/health", get(health))
        .route("/info", get(info))
        .route("/visits", get(visits).post(add_visit))
        .layer(CorsLayer::permissive());

    let port = env::var("PORT").unwrap_or("8000".into());
    let listener = tokio::net::TcpListener::bind(format!("0.0.0.0:{port}")).await.unwrap();
    println!("rust listening on {port}");
    axum::serve(listener, app).await.unwrap();
}

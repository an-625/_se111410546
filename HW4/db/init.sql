-- 微服務共用資料庫初始化
CREATE TABLE IF NOT EXISTS visits (
    id SERIAL PRIMARY KEY,
    service VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system_info (
    key VARCHAR(50) PRIMARY KEY,
    value TEXT
);

INSERT INTO visits(service) VALUES ('init'), ('node'), ('rust'), ('python')
ON CONFLICT DO NOTHING;

INSERT INTO system_info(key, value) VALUES
    ('project', 'docker-micro-system'),
    ('stack', 'nginx + node + rust + python + postgres')
ON CONFLICT (key) DO NOTHING;

# HW1: mini-curl — 類似 curl 的命令列 HTTP 工具

只用 Python 標準函式庫 (`urllib`)，不用安裝任何套件。

## 執行

```bash
python mini_curl.py [選項] URL
```

## 範例

```bash
# 基本 GET
python mini_curl.py https://example.com

# POST JSON
python mini_curl.py -X POST -H "Content-Type: application/json" \
  -d '{"name":"王小明"}' https://httpbin.org/post

# 存檔
python mini_curl.py -o page.html https://example.com

# 顯示回應標頭 + 除錯細節
python mini_curl.py -i -v https://httpbin.org/get

# 自訂標頭 + PUT
python mini_curl.py -X PUT -H "X-Token: abc123" -d 'hi' https://httpbin.org/put

# 安靜模式 (只印 body，適合接管線)
python mini_curl.py -s https://httpbin.org/ip
```

## 選項

| 選項 | 說明 |
|------|------|
| `-X, --request` | HTTP 方法 (GET/POST/PUT/DELETE…，有 `-d` 時預設 POST) |
| `-H, --header` | 自訂標頭 `"Key: Value"`，可重複 |
| `-d, --data` | 請求 body |
| `-o, --output` | 存檔 (預設印螢幕) |
| `-i, --include` | 同時顯示回應標頭 |
| `-v, --verbose` | 顯示請求/回應細節 |
| `-s, --silent` | 安靜模式 |
| `-A, --user-agent` | 自訂 User-Agent |
| `--timeout` | 逾時秒數 (預設 15) |
| `--fail` | 狀態碼 ≥400 時以非零結束 |

## 特色

- JSON 回應自動排版
- 顯示狀態碼 / 大小 / 花費時間 (stderr，不污染管線輸出)
- HTTP 錯誤會印到 stderr；`--fail` 可讓結束碼非零，方便寫腳本判斷

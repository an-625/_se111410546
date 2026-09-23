"""mini-curl:類似 curl 的輕量命令列 HTTP 工具 (只用 Python 標準函式庫,免安裝).

用法:
    python mini_curl.py [選項] URL

範例:
    python mini_curl.py https://example.com
    python mini_curl.py -X POST -H "Content-Type: application/json" \\
        -d '{"name":"王小明"}' https://httpbin.org/post
    python mini_curl.py -o page.html https://example.com
    python mini_curl.py -i -v https://httpbin.org/get
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="mini_curl",
        description="類似 curl 的輕量 HTTP 工具 (GET/POST/PUT/DELETE...)",
    )
    p.add_argument("url", help="請求的 URL")
    p.add_argument("-X", "--request", default=None,
                   help="HTTP 方法,如 GET/POST/PUT/DELETE (預設 GET,有 -d 時預設 POST)")
    p.add_argument("-H", "--header", action="append", default=[],
                   metavar='"Key: Value"', help="自訂請求標頭,可重複使用")
    p.add_argument("-d", "--data", default=None, help="請求 body (字串)")
    p.add_argument("-o", "--output", default=None, help="把回應存檔 (預設印到螢幕)")
    p.add_argument("-i", "--include", action="store_true", help="同時顯示回應標頭")
    p.add_argument("-v", "--verbose", action="store_true", help="顯示請求/回應細節")
    p.add_argument("-s", "--silent", action="store_true", help="安靜模式(只輸出 body)")
    p.add_argument("-A", "--user-agent", default="mini-curl/1.0",
                   help="User-Agent (預設 mini-curl/1.0)")
    p.add_argument("--timeout", type=float, default=15, help="逾時秒數 (預設 15)")
    p.add_argument("--fail", action="store_true",
                   help="HTTP 狀態 >=400 時以非零結束 (像 curl -f)")
    return p.parse_args(argv)


def build_request(args):
    method = (args.request or ("POST" if args.data is not None else "GET")).upper()
    body = args.data.encode("utf-8") if args.data is not None else None
    req = urllib.request.Request(args.url, data=body, method=method)
    req.add_header("User-Agent", args.user_agent)
    for h in args.header:
        if ":" not in h:
            print(f"標頭格式錯誤 (應為 Key: Value): {h}", file=sys.stderr)
            return None
        k, v = h.split(":", 1)
        req.add_header(k.strip(), v.strip())
    return req


def main(argv=None):
    args = parse_args(argv)
    req = build_request(args)
    if req is None:
        return 2

    verb = lambda *a: print(*a, file=sys.stderr) if args.verbose and not args.silent else None
    verb(f"> {req.get_method()} {args.url}")
    for k, v in req.header_items():
        verb(f"> {k}: {v}")

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            status, headers, raw = resp.status, resp.headers, resp.read()
            final_url = resp.geturl()
    except urllib.error.HTTPError as e:
        status, headers, raw = e.code, e.headers, e.read()
        final_url = e.geturl()
        if not args.silent:
            print(f"HTTP 錯誤: {status}", file=sys.stderr)
    except Exception as e:  # 連線失敗 / 逾時 / URL 錯誤
        if not args.silent:
            print(f"請求失敗: {e}", file=sys.stderr)
        return 1
    dt = time.time() - t0

    verb(f"< HTTP {status} ({dt:.2f}s) final-url: {final_url}")
    if args.verbose and not args.silent:
        for k, v in (headers.items() if headers else []):
            print(f"< {k}: {v}", file=sys.stderr)

    ctype = (headers.get("Content-Type", "") if headers else "")
    text = raw.decode("utf-8", errors="replace")
    pretty = text
    if "json" in ctype:  # JSON 自動排版
        try:
            pretty = json.dumps(json.loads(text), ensure_ascii=False, indent=2)
        except (ValueError, TypeError):
            pass

    if args.include and not args.silent:
        print(f"HTTP {status}")
        for k, v in (headers.items() if headers else []):
            print(f"{k}: {v}")
        print()
    if args.output:
        mode = "w" if "json" in ctype or "text" in ctype or "html" in ctype or "xml" in ctype else "wb"
        with open(args.output, mode, encoding="utf-8" if mode == "w" else None) as f:
            f.write(pretty if mode == "w" else raw)
        if not args.silent:
            print(f"已存檔: {args.output} ({len(raw)} bytes, {dt:.2f}s)")
    else:
        print(pretty if ("json" in ctype) else text, end="" if text.endswith("\n") else "\n")
    if not args.silent and not args.output:
        print(f"[status={status} size={len(raw)}B time={dt:.2f}s]", file=sys.stderr)

    if args.fail and status >= 400:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

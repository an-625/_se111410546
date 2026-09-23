"""mini-backup:增量備份工具 (只用 Python 標準函式庫,免安裝).

每次備份只複製「新增 / 修改過」的檔案 (用 SHA-256 判斷),
沒變的檔案沿用舊快照,還原時自動從快照鏈拼回完整狀態.

用法:
    python mini_backup.py backup 來源 備份倉庫 [--exclude "*.tmp"]
    python mini_backup.py list 備份倉庫
    python mini_backup.py restore 備份倉庫 快照ID 還原目標
    python mini_backup.py verify 備份倉庫 快照ID
    python mini_backup.py prune 備份倉庫 --keep 5
    python mini_backup.py status 備份倉庫

範例:
    python mini_backup.py backup D:\\報告 D:\\備份
    python mini_backup.py backup D:\\報告 D:\\備份 --dry-run
    python mini_backup.py restore D:\\備份 20260923_093000 D:\\還原
"""
import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime

CHUNK = 1024 * 1024


def fs(rel):
    """manifest 內一律用 / ,轉回本機檔案系統路徑."""
    return rel.replace("/", os.sep)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def snap_dir(repo):
    return os.path.join(repo, "snapshots")


def mani_path(repo, sid):
    return os.path.join(repo, "manifests", sid + ".json")


def all_snapshots(repo):
    """回傳排序過的快照 ID 清單 (舊 -> 新)."""
    d = os.path.join(repo, "manifests")
    if not os.path.isdir(d):
        return []
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))


def load_manifest(repo, sid):
    with open(mani_path(repo, sid), encoding="utf-8") as f:
        return json.load(f)


def scan(source, excludes):
    """走訪來源,回傳 {相對路徑: 絕對路徑} (套用排除規則)."""
    found = {}
    for root, _dirs, files in os.walk(source):
        for name in files:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, source).replace(os.sep, "/")
            if any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(name, p) for p in excludes):
                continue
            found[rel] = full
    return found


def new_snapshot_id(repo):
    base = datetime.now().strftime("%Y%m%d_%H%M%S")
    sid, n = base, 1
    while os.path.exists(mani_path(repo, sid)):
        n += 1
        sid = f"{base}_{n}"
    return sid


# ---------- backup ----------
def cmd_backup(a):
    src = os.path.abspath(a.source)
    if not os.path.isdir(src):
        print(f"來源不存在: {src}", file=sys.stderr)
        return 1
    os.makedirs(snap_dir(a.repo), exist_ok=True)
    os.makedirs(os.path.join(a.repo, "manifests"), exist_ok=True)

    prev_list = all_snapshots(a.repo)
    prev_files = load_manifest(a.repo, prev_list[-1])["files"] if prev_list else {}
    current = scan(src, a.exclude or [])

    sid = new_snapshot_id(a.repo)
    snap_path = os.path.join(snap_dir(a.repo), sid)
    files, added, modified, unchanged = {}, 0, 0, 0
    copied_bytes = 0
    for rel, full in sorted(current.items()):
        digest = sha256_of(full)
        old = prev_files.get(rel)
        if old and not old.get("deleted") and old.get("hash") == digest:
            files[rel] = old  # 沒變:沿用舊快照內容
            unchanged += 1
            continue
        size = os.path.getsize(full)
        if not a.dry_run:
            dst = os.path.join(snap_path, fs(rel))
            os.makedirs(os.path.dirname(dst) or snap_path, exist_ok=True)
            shutil.copy2(full, dst)
        files[rel] = {"hash": digest, "size": size, "snapshot": sid}
        copied_bytes += size
        if old and not old.get("deleted"):
            modified += 1
        else:
            added += 1
    deleted = sorted(set(prev_files) - set(current) - {r for r, e in prev_files.items() if e.get("deleted")})
    for rel in deleted:
        files[rel] = {"deleted": True}

    if a.dry_run:
        print(f"[試跑] 快照 {sid}: 新增 {added}, 修改 {modified}, "
              f"刪除 {len(deleted)}, 未變更 {unchanged}, 需複製 {copied_bytes} bytes")
        return 0
    manifest = {"id": sid, "time": datetime.now().isoformat(timespec="seconds"),
                "source": src, "files": files}
    with open(mani_path(a.repo, sid), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    live = sum(1 for e in files.values() if not e.get("deleted"))
    print(f"備份完成: {sid} (新增 {added}, 修改 {modified}, "
          f"刪除 {len(deleted)}, 未變更 {unchanged}, 共 {live} 個檔案, {copied_bytes} bytes)")
    return 0


# ---------- list ----------
def cmd_list(a):
    ids = all_snapshots(a.repo)
    if not ids:
        print("尚無快照")
        return 0
    for sid in ids:
        m = load_manifest(a.repo, sid)
        live = sum(1 for e in m["files"].values() if not e.get("deleted"))
        print(f"{sid}  {m['time']}  {live} 個檔案")
    return 0


# ---------- restore ----------
def restore_manifest(repo, sid, target):
    m = load_manifest(repo, sid)
    ok, missing = 0, []
    for rel, e in sorted(m["files"].items()):
        if e.get("deleted"):
            continue
        content = os.path.join(snap_dir(repo), e["snapshot"], fs(rel))
        if not os.path.isfile(content):
            missing.append(rel)
            continue
        dst = os.path.join(target, fs(rel))
        os.makedirs(os.path.dirname(dst) or target, exist_ok=True)
        shutil.copy2(content, dst)
        ok += 1
    return ok, missing


def cmd_restore(a):
    if a.snapshot not in all_snapshots(a.repo):
        print(f"找不到快照: {a.snapshot}", file=sys.stderr)
        return 1
    ok, missing = restore_manifest(a.repo, a.snapshot, os.path.abspath(a.target))
    print(f"還原完成: {ok} 個檔案 -> {a.target}")
    if missing:
        print(f"警告: {len(missing)} 個檔案內容遺失:", file=sys.stderr)
        for rel in missing:
            print(f"  ! {rel}", file=sys.stderr)
        return 1
    return 0


# ---------- verify ----------
def cmd_verify(a):
    if a.snapshot not in all_snapshots(a.repo):
        print(f"找不到快照: {a.snapshot}", file=sys.stderr)
        return 1
    m = load_manifest(a.repo, a.snapshot)
    bad, checked = [], 0
    for rel, e in sorted(m["files"].items()):
        if e.get("deleted"):
            continue
        checked += 1
        content = os.path.join(snap_dir(a.repo), e["snapshot"], fs(rel))
        if not os.path.isfile(content) or sha256_of(content) != e["hash"]:
            bad.append(rel)
    if bad:
        print(f"驗證失敗: {len(bad)}/{checked} 個檔案損壞或遺失:")
        for rel in bad:
            print(f"  ! {rel}")
        return 1
    print(f"驗證通過: {checked} 個檔案皆正常 ({a.snapshot})")
    return 0


# ---------- prune ----------
def cmd_prune(a):
    ids = all_snapshots(a.repo)
    if len(ids) <= a.keep:
        print(f"快照只有 {len(ids)} 個,不需清理 (keep={a.keep})")
        return 0
    keep, drop = set(ids[-a.keep:]), ids[:-a.keep]
    newest = ids[-1]
    # 被刪快照若仍有內容被保留的快照引用,先搬進最新快照並修正指向
    for sid in sorted(keep):
        m = load_manifest(a.repo, sid)
        changed = False
        for rel, e in m["files"].items():
            if e.get("deleted") or e["snapshot"] not in drop:
                continue
            src = os.path.join(snap_dir(a.repo), e["snapshot"], fs(rel))
            dst = os.path.join(snap_dir(a.repo), newest, fs(rel))
            if os.path.isfile(src):
                os.makedirs(os.path.dirname(dst) or os.path.join(snap_dir(a.repo), newest),
                            exist_ok=True)
                if not os.path.isfile(dst):
                    shutil.copy2(src, dst)
                e["snapshot"] = newest
                changed = True
        if changed:
            with open(mani_path(a.repo, sid), "w", encoding="utf-8") as f:
                json.dump(m, f, ensure_ascii=False, indent=2)
    for sid in drop:
        shutil.rmtree(os.path.join(snap_dir(a.repo), sid), ignore_errors=True)
        os.remove(mani_path(a.repo, sid))
    print(f"清理完成: 刪除 {len(drop)} 個舊快照,保留 {len(keep)} 個")
    return 0


# ---------- status ----------
def dir_size(path):
    total = 0
    for _root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(_root, name))
            except OSError:
                pass
    return total


def cmd_status(a):
    ids = all_snapshots(a.repo)
    print(f"倉庫: {os.path.abspath(a.repo)}")
    print(f"快照數: {len(ids)}")
    if ids:
        print(f"最新: {ids[-1]}")
    print(f"佔用: {dir_size(a.repo)} bytes")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="mini_backup", description="增量備份工具")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("backup", help="備份來源到倉庫")
    b.add_argument("source")
    b.add_argument("repo")
    b.add_argument("--exclude", action="append", default=[], help="排除規則,可重複")
    b.add_argument("--dry-run", action="store_true", help="只顯示變更,不真的備份")
    b.set_defaults(func=cmd_backup)

    l = sub.add_parser("list", help="列出快照")
    l.add_argument("repo")
    l.set_defaults(func=cmd_list)

    r = sub.add_parser("restore", help="還原快照")
    r.add_argument("repo")
    r.add_argument("snapshot")
    r.add_argument("target")
    r.set_defaults(func=cmd_restore)

    v = sub.add_parser("verify", help="驗證快照完整性")
    v.add_argument("repo")
    v.add_argument("snapshot")
    v.set_defaults(func=cmd_verify)

    pr = sub.add_parser("prune", help="清理舊快照")
    pr.add_argument("repo")
    pr.add_argument("--keep", type=int, default=5, help="保留最新幾個 (預設 5)")
    pr.set_defaults(func=cmd_prune)

    s = sub.add_parser("status", help="倉庫狀態")
    s.add_argument("repo")
    s.set_defaults(func=cmd_status)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

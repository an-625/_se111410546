# HW3: mini-backup — 增量備份工具

只用 Python 標準函式庫，免安裝。每次備份只複製「新增 / 修改過」的檔案
（用 SHA-256 判斷），沒變的沿用舊快照，還原時自動從快照鏈拼回完整狀態。

## 指令

```bash
python mini_backup.py backup 來源 備份倉庫 [--exclude "*.tmp"] [--dry-run]
python mini_backup.py list 備份倉庫
python mini_backup.py restore 備份倉庫 快照ID 還原目標
python mini_backup.py verify 備份倉庫 快照ID
python mini_backup.py prune 備份倉庫 --keep 5
python mini_backup.py status 備份倉庫
```

## 範例

```bash
# 備份 D 槽報告到備份倉庫 (先試跑看看會備什麼)
python mini_backup.py backup D:\報告 D:\備份 --dry-run

# 真的備份 (排除暫存檔)
python mini_backup.py backup D:\報告 D:\備份 --exclude "*.tmp" --exclude "~*"

# 看有哪些快照
python mini_backup.py list D:\備份
# 20260923_093000  2026-09-23T09:30:00  42 個檔案
# 20260923_180000  2026-09-23T18:00:00  43 個檔案

# 還原某個時間點的完整狀態
python mini_backup.py restore D:\備份 20260923_093000 D:\還原

# 驗證備份有沒有損壞
python mini_backup.py verify D:\備份 20260923_180000

# 只留最新 5 個快照 (被舊快照引用的內容會自動搬進最新快照，不會斷鏈)
python mini_backup.py prune D:\備份 --keep 5
```

## 設計

- `備份倉庫/snapshots/<快照ID>/`：該次實際複製的檔案（只有新增/修改的）
- `備份倉庫/manifests/<快照ID>.json`：該時間點的完整檔案清單，每個檔記載
  SHA-256 與內容放在哪個快照，刪除的檔記 `deleted`
- 還原/驗證時按 manifest 的指向取內容；prune 會先把仍被引用的內容搬進
  最新快照再刪舊快照，所以鏈不會斷

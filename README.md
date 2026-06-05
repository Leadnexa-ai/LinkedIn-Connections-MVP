# LinkedIn Connections MVP

Semi-automatic LinkedIn connection capture workflow using Google Sheets as the source of truth.

使用 Google Sheet 作为主数据库的半自动 LinkedIn connections 抓取流程。

## Overview / 概览

This project does three things:

这个项目完成三件事：

1. Read active rows from a Google Sheet and generate `profiles.csv`
2. Open each LinkedIn profile with Selenium and capture the latest connection count
3. Write the latest result back to the same Google Sheet

1. 从 Google Sheet 读取有效行并生成 `profiles.csv`
2. 使用 Selenium 打开每个 LinkedIn profile，抓取最新的 connection 数量
3. 将最新结果回写到同一张 Google Sheet

## Requirements / 环境要求

- Google Chrome installed locally
- Python virtual environment in `.venv`
- A Google service account JSON key file
- A Google Sheet shared with that service account as `Editor`

- 本机已安装 Google Chrome
- 项目目录中已有 `.venv` Python 虚拟环境
- 已下载 Google service account 的 JSON key 文件
- 已将该 service account 以 `Editor` 权限分享进 Google Sheet

## Install / 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
.venv/bin/python3 -m pip install -r requirements.txt
```

## Files / 文件说明

- `google_service_account.json`: local Google service account credentials
- `profiles.csv`: generated runtime input for Selenium
- `linkedin_connections.csv`: latest capture result in CSV
- `linkedin_connections.xlsx`: latest capture result in Excel
- `generate_profiles_from_google_sheet.py`: build `profiles.csv` from Google Sheet
- `update_google_sheet_from_results.py`: write capture results back to Google Sheet

- `google_service_account.json`：本地 Google service account 凭证
- `profiles.csv`：运行时生成的 Selenium 输入文件
- `linkedin_connections.csv`：最新抓取结果 CSV
- `linkedin_connections.xlsx`：最新抓取结果 Excel
- `generate_profiles_from_google_sheet.py`：从 Google Sheet 生成 `profiles.csv`
- `update_google_sheet_from_results.py`：将抓取结果回写到 Google Sheet

## Google Sheet Structure / Google Sheet 表结构

Use these headers in `Sheet1`:

请在 `Sheet1` 中使用以下表头：

```text
profile_name,name,linkedin_url,last_connections_number,last_checked_at,active
```

Field meaning:

字段说明：

- `profile_name`: internal profile identifier
- `name`: expected person name
- `linkedin_url`: LinkedIn profile URL
- `last_connections_number`: last successful captured number
- `last_checked_at`: last successful update timestamp
- `active`: optional flag to include or skip a row

- `profile_name`：内部 profile 标识
- `name`：预期的人名
- `linkedin_url`：LinkedIn profile 链接
- `last_connections_number`：上一次成功抓取的数量
- `last_checked_at`：上一次成功更新时间
- `active`：可选开关，用来决定本次是否参与运行

`active` behavior:

`active` 规则：

- blank / empty = included
- `TRUE`, `YES`, `1`, `ACTIVE` = included
- any other value = skipped

- 留空 = 参与运行
- `TRUE`、`YES`、`1`、`ACTIVE` = 参与运行
- 其他值 = 跳过

## Main Workflow / 主流程

### 1. Generate `profiles.csv` from Google Sheet

### 1. 从 Google Sheet 生成 `profiles.csv`

```bash
.venv/bin/python3 generate_profiles_from_google_sheet.py \
  --credentials google_service_account.json \
  --sheet "YOUR_GOOGLE_SHEET_URL" \
  --worksheet "Sheet1" \
  --out profiles.csv
```

Expected output:

预期输出：

- sheet row count
- active row count
- skipped row count
- generated `profiles.csv` row count

- Sheet 总行数
- 参与运行的行数
- 被跳过的行数
- 生成的 `profiles.csv` 行数

### 2. Run LinkedIn capture

### 2. 运行 LinkedIn 抓取

```bash
.venv/bin/python3 linkedin_connections_mvp.py \
  --input profiles.csv \
  --out linkedin_connections.csv \
  --xlsx linkedin_connections.xlsx
```

During this step:

这一步中：

1. Chrome opens with the local Selenium profile
2. You log in manually if needed
3. The script opens each LinkedIn URL
4. The script captures the visible `connections` number only

1. Chrome 会使用本地 Selenium profile 打开
2. 如有需要，你手动登录
3. 脚本逐个打开 LinkedIn URL
4. 脚本只抓取页面可见的 `connections` 数量

### 3. Write results back to Google Sheet

### 3. 将结果回写到 Google Sheet

```bash
.venv/bin/python3 update_google_sheet_from_results.py \
  --credentials google_service_account.json \
  --sheet "YOUR_GOOGLE_SHEET_URL" \
  --worksheet "Sheet1" \
  --results linkedin_connections.csv
```

This updates:

这一步会更新：

- `name`
- `linkedin_url`
- `last_connections_number`
- `last_checked_at`

## Result Format / 结果格式

`linkedin_connections.csv` and `linkedin_connections.xlsx` use:

`linkedin_connections.csv` 和 `linkedin_connections.xlsx` 使用以下字段：

```text
profile_name,name,url,original_connections_number,recent_connections_number
```

Meaning:

字段含义：

- `original_connections_number`: previous value from Google Sheet
- `recent_connections_number`: newly captured value from LinkedIn

- `original_connections_number`：来自 Google Sheet 的上次记录
- `recent_connections_number`：本次从 LinkedIn 新抓到的值

## Notes / 注意事项

- `google_service_account.json` is local-only and must not be committed to Git
- `profiles.csv` is generated each run and should not be treated as the source of truth
- The Google Sheet is now the primary database
- Manual LinkedIn login is still required when the browser session expires

- `google_service_account.json` 只用于本地，不要提交到 Git
- `profiles.csv` 每次运行都会重新生成，不应作为主数据库
- Google Sheet 现在是主数据库
- 当浏览器登录状态过期时，仍然需要手动登录 LinkedIn

## Troubleshooting / 常见问题

### Google Sheet API works but rows are skipped

### Google Sheet API 正常，但有些行被跳过

Check:

请检查：

- `linkedin_url` is not empty
- `active` is blank or allowed
- `profile_name` is present

- `linkedin_url` 不为空
- `active` 为留空或允许值
- `profile_name` 已填写

### Selenium cannot import modules

### Selenium 模块导入失败

Use the virtual environment Python:

请使用虚拟环境里的 Python：

```bash
.venv/bin/python3 linkedin_connections_mvp.py --input profiles.csv --out linkedin_connections.csv --xlsx linkedin_connections.xlsx
```

### Google Sheet access denied

### Google Sheet 权限报错

Check:

请检查：

- `Google Sheets API` is enabled
- `Google Drive API` is enabled
- the service account `client_email` has `Editor` access to the sheet

- 已启用 `Google Sheets API`
- 已启用 `Google Drive API`
- service account 的 `client_email` 已被授予该表格的 `Editor` 权限

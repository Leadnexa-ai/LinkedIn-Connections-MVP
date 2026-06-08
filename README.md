# LinkedIn Connections MVP

Semi-automatic LinkedIn connection capture workflow using Supabase as the source of truth.

使用 Supabase 作为主数据库的半自动 LinkedIn connections 抓取流程。

## Overview / 概览

This project does three things:

这个项目完成三件事：

1. Read active rows from Supabase and generate `profiles.csv`
2. Open each LinkedIn profile with Selenium and capture the latest connection count
3. Write the latest result back to Supabase

1. 从 Supabase 读取有效行并生成 `profiles.csv`
2. 使用 Selenium 打开每个 LinkedIn profile，抓取最新的 connection 数量
3. 将最新结果回写到 Supabase

## Requirements / 环境要求

- Google Chrome installed locally
- Python virtual environment in `.venv`
- A Supabase project URL
- A Supabase API key stored locally in `.env`
- A Supabase table for LinkedIn profiles

- 本机已安装 Google Chrome
- 项目目录中已有 `.venv` Python 虚拟环境
- 一个 Supabase 项目 URL
- 一个保存在本地 `.env` 中的 Supabase API key
- 一个用于存储 LinkedIn profiles 的 Supabase 表

## Install / 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
.venv/bin/python3 -m pip install -r requirements.txt
```

## Local Config / 本地配置

Do not paste your Supabase key into chat. Put it in local `.env` instead.

不要把 Supabase key 发在聊天里，直接填到本地 `.env`。

Use this structure:

请使用以下结构：

```env
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_KEY
SUPABASE_TABLE=profiles
```

`SUPABASE_SERVICE_ROLE_KEY` is recommended because this workflow reads and writes rows.

推荐使用 `SUPABASE_SERVICE_ROLE_KEY`，因为这条流程需要读写数据库。

## Supabase Table Structure / Supabase 表结构

Use these columns in your Supabase table.

Minimum required:

请在 Supabase 表中使用以下字段。

最低必需字段：

```text
profile_name,name,linkedin_url,active
```

Optional but recommended:

推荐附加字段：

```text
last_connections_number,last_checked_at
```

Field meaning:

字段说明：

- `profile_name`: internal profile identifier
- `name`: expected person name
- `linkedin_url`: LinkedIn profile URL
- `active`: optional flag to include or skip a row
- `last_connections_number`: last successful captured number
- `last_checked_at`: last successful update timestamp

- `profile_name`：内部 profile 标识
- `name`：预期的人名
- `linkedin_url`：LinkedIn profile 链接
- `active`：可选开关，用来决定本次是否参与运行
- `last_connections_number`：上一次成功抓取的数量
- `last_checked_at`：上一次成功更新时间

`active` behavior:

`active` 规则：

- blank / empty = included
- `TRUE`, `YES`, `1`, `ACTIVE` = included
- any other value = skipped

- 留空 = 参与运行
- `TRUE`、`YES`、`1`、`ACTIVE` = 参与运行
- 其他值 = 跳过

## Files / 文件说明

- `supabase_sync.py`: Supabase read/write helpers
- `generate_profiles_from_supabase.py`: build `profiles.csv` from Supabase
- `update_supabase_from_results.py`: write capture results back to Supabase
- `profiles.csv`: generated runtime input for Selenium
- `linkedin_connections.csv`: latest capture result in CSV
- `linkedin_connections.xlsx`: latest capture result in Excel

- `supabase_sync.py`：Supabase 读写辅助函数
- `generate_profiles_from_supabase.py`：从 Supabase 生成 `profiles.csv`
- `update_supabase_from_results.py`：将抓取结果回写到 Supabase
- `profiles.csv`：运行时生成的 Selenium 输入文件
- `linkedin_connections.csv`：最新抓取结果 CSV
- `linkedin_connections.xlsx`：最新抓取结果 Excel

## Main Workflow / 主流程

### 1. Generate `profiles.csv` from Supabase

### 1. 从 Supabase 生成 `profiles.csv`

```bash
.venv/bin/python3 generate_profiles_from_supabase.py --env-file .env --out profiles.csv
```

Expected output:

预期输出：

- Supabase row count
- active row count
- skipped row count
- generated `profiles.csv` row count

- Supabase 总行数
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

### 3. Write results back to Supabase

### 3. 将结果回写到 Supabase

```bash
.venv/bin/python3 update_supabase_from_results.py --env-file .env --results linkedin_connections.csv
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

- `original_connections_number`: previous value from Supabase
- `recent_connections_number`: newly captured value from LinkedIn

- `original_connections_number`：来自 Supabase 的上次记录
- `recent_connections_number`：本次从 LinkedIn 新抓到的值

## Notes / 注意事项

- `.env` is local-only and must not be committed to Git
- `profiles.csv` is generated each run and should not be treated as the source of truth
- Supabase is now the primary database
- Manual LinkedIn login is still required when the browser session expires

- `.env` 只用于本地，不要提交到 Git
- `profiles.csv` 每次运行都会重新生成，不应作为主数据库
- Supabase 现在是主数据库
- 当浏览器登录状态过期时，仍然需要手动登录 LinkedIn

## Troubleshooting / 常见问题

### Supabase rows are skipped

### Supabase 有些行被跳过

Check:

请检查：

- `linkedin_url` is not empty
- `active` is blank or allowed
- `profile_name` is present

- `linkedin_url` 不为空
- `active` 为留空或允许值
- `profile_name` 已填写

### Supabase updates fail

### Supabase 回写失败

Check:

请检查：

- `SUPABASE_URL` is correct
- `SUPABASE_SERVICE_ROLE_KEY` has write permission
- table name in `.env` matches your actual table, for example `profiles`
- `SUPABASE_URL` 正确
- `SUPABASE_SERVICE_ROLE_KEY` 具有写权限
- `.env` 中的表名与你真实表名一致

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

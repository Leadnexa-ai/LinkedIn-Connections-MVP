# LinkedIn Connections MVP

半自动 Selenium 小工具：打开你提供的 LinkedIn URL，人工登录后，脚本逐页自动读取 `connections` 文本，并按本次输入刷新 CSV，可选导出 Excel。

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

需要本机已安装 Google Chrome。新版 Selenium 通常会自动管理 ChromeDriver；如果你的环境不支持，可以下载对应版本的 ChromeDriver，然后运行时传 `--driver-path`。

## 准备 URL

复制模板生成你自己的输入文件：

```bash
cp profiles.example.csv profiles.csv
```

然后把 profile name 和 LinkedIn URL 放进 `profiles.csv`：

```csv
profile_name,url,original_connections_number
USUT13A,https://www.linkedin.com/in/eleanor-king-325186403,
USTMJ09E,https://www.linkedin.com/in/hazel-carter-036578403,
USNJ06G,https://www.linkedin.com/in/indira-torres-9422283ba/,
```

`original_connections_number` 可以留空。脚本会自动从 LinkedIn 页面读取人物姓名和最新 connections 数量。

如果 `original_connections_number` 留空，脚本会优先使用上一次输出文件中同一个 `profile_name + url` 的 `recent_connections_number` 作为本次 original。这样每次运行都可以得到“上次数量 vs 本次数量”。

旧格式也可以继续用：把 LinkedIn URL 放进本地 `urls.txt`，一行一个：

```text
https://www.linkedin.com/in/some-profile/
https://www.linkedin.com/in/another-profile/
```

## 运行

```bash
python3 linkedin_connections_mvp.py --input profiles.csv --out linkedin_connections.csv --xlsx linkedin_connections.xlsx
```

运行后：

1. Chrome 会打开第一个 URL。
2. 你在浏览器里手动完成 Google/LinkedIn 登录。
3. 回到终端按回车。
4. 脚本逐个打开页面，只查找 `connections` 文本。
5. 找到后写入 CSV；输出文件每次都会刷新，不会叠加旧 run 的记录。

脚本不会读取 `followers`、推荐账号数字或页面里其他无关数字。

## 常用参数

```bash
python3 linkedin_connections_mvp.py --start-index 20
python3 linkedin_connections_mvp.py --delay 3
python3 linkedin_connections_mvp.py --profile-dir .selenium-profile
```

- `--start-index`：从第几个 URL 继续，适合中断后恢复。
- `--delay`：每个页面之间的等待秒数。
- `--profile-dir`：Chrome 登录状态保存目录，默认 `.selenium-profile`。
- `--input`：包含 `profile_name` 和 `url` 的输入 CSV，默认 `profiles.csv`。
- `--xlsx`：可选 Excel 输出路径，不传就只写 CSV。

## 输出字段

- `profile_name`
- `name`
- `url`
- `original_connections_number`
- `recent_connections_number`

## CSV Database Workflow

试验阶段可以用本地 CSV 当 database。先复制模板：

```bash
cp profiles_database.example.csv profiles_database.csv
cp folder_profiles.example.csv folder_profiles.csv
```

`profiles_database.csv` 是完整资料库：

```csv
profile_name,name,linkedin_url,last_connections_number,last_checked_at
USUT13A,Eleanor King,https://www.linkedin.com/in/example-profile-1,,
```

`folder_profiles.csv` 表示这次要跑的 Multilogin folder profile name 列表：

```csv
profile_name
USUT13A
USNJ06G
```

生成本次抓取用的 `profiles.csv`：

```bash
python3 generate_profiles_from_database.py --database profiles_database.csv --folder folder_profiles.csv --out profiles.csv
```

运行 LinkedIn 抓取：

```bash
python3 linkedin_connections_mvp.py --input profiles.csv --out linkedin_connections.csv --xlsx linkedin_connections.xlsx
```

抓取完成后，把本次结果回写到 database：

```bash
python3 update_database_from_results.py --database profiles_database.csv --results linkedin_connections.csv
```

下一次再生成 `profiles.csv` 时，`last_connections_number` 会自动变成 `original_connections_number`。

## Multilogin

当前仓库先预留了 `.env.example`，真实 API token 不要提交到 Git。

```bash
cp .env.example .env
```

之后接 Multilogin API 时，脚本会用 folder id 生成 `folder_profiles.csv`，再沿用上面的 CSV database workflow。

请只处理你有权限查看的页面，并遵守 LinkedIn 的使用条款和访问频率限制。

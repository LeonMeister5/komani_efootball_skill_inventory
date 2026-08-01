# Notes of LeonMeister

Below is all ChatGPT bullshit. This is a project created to store 0 GP players with 1 skill, and by merging them with good players, good player gain that skill at the cost of 250000GP. 

I want to keep track of my 0 GP players with 1 skill, therefore develop this project in 15 minutes with Codex. 

------ Important: double click ./dist/实况足球技能仓库/实况足球技能仓库.exe to use. Always remember saving your data by clicking one of those buttons. 

This shit is all in Chinese, therefore feel free to feed all those AI shits to codex and generate this same project (or better) in your language. 

Have fun, thank you. :)

我草国际服真良心吧














# 实况足球技能仓库

一个面向 Windows 11 的离线桌面应用，用于管理 eFootball 一星球员技能载体。每条球员记录代表一张独立卡片，并且恰好关联一个技能。SQLite 是唯一真实数据源，不需要账号、服务器或浏览器。

## 功能介绍

- 按球员姓名或技能名称进行不区分大小写的模糊搜索，并按技能、状态筛选
- 使用可排序的 `ttk.Treeview` 展示库存；双击即可编辑
- 新增、编辑、删除同名球员卡，快速切换可用、已预留、已消耗状态
- 独立管理技能名称、分类和启用状态，并查看各状态数量
- 记录新增、编辑、删除、状态变化、技能变化和 CSV 导入历史
- 导入前预览 CSV，逐行校验和提交，自动创建缺失技能并报告错误行
- 导出带 UTF-8 BOM 的 CSV，方便 Windows Excel 正确显示中文
- 使用 SQLite 在线备份 API 自动/手动备份，并自动清理旧备份
- 显示库存数量、累计创建成本、当前可用价值和低库存技能
- 支持系统、浅色、深色主题，并记住上次选择

## 项目截图

当前仓库未附带截图。启动后可将主窗口截图放入 `docs/screenshot.png`，再在此处引用。

## 环境要求

- Windows 11
- Python 3.12 或兼容版本
- 依赖：CustomTkinter、pytest、PyInstaller；数据访问只使用标准库 `sqlite3`，未引入 ORM

## 安装与运行

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

也可以双击 `run.bat`；脚本会优先使用 `.venv\Scripts\python.exe`，否则使用系统 `python`。

首次启动技能表为空。请先点击“技能管理”添加技能，再新增球员载体。

## 测试

```powershell
python -m pytest -q
```

核心测试不启动 GUI，会使用临时目录中的独立 SQLite 数据库。

## 打包 EXE

先安装依赖，然后双击 `build.bat`，或在命令行运行它。脚本会清理旧 `build`/`dist`，以 `--noconsole` 模式打包，输出到：

```text
dist\实况足球技能仓库\实况足球技能仓库.exe
```

数据库不会打包进 EXE。CustomTkinter 的主题资源由 `--collect-all customtkinter` 一并收集。没有图标文件也不影响构建。

## 数据位置与安全

所有运行数据都位于：

```text
%LOCALAPPDATA%\EFootballSkillManager\
├─ efootball.db
├─ backups\
├─ exports\
└─ logs\app.log
```

程序首次启动自动创建目录和数据库。每次正常启动会在启用自动备份时创建备份；CSV 导入前也会先备份。备份使用 SQLite backup API 取得一致性快照，默认保留最新 20 份。物理删除球员后，完整 JSON 快照仍保留在操作历史中，因此累计创建成本不会下降。

建议定期把 `backups` 目录复制到另一块磁盘。不要在应用运行中手动替换数据库文件。日志只记录操作类型和异常信息，不主动写入无关隐私数据。

## CSV 格式

导出列为：

```text
id,player_name,skill_name,status,reserved_for,consumed_for,note,created_at,updated_at,consumed_at
```

导入必填列为 `player_name`、`skill_name`、`status`。`status` 只能是 `available`、`reserved` 或 `consumed`；其余列可选。导入文件支持 UTF-8 或 UTF-8 BOM。某行失败不会回滚其他成功行，结果窗口会列出错误行号和原因。

## 常见问题

- **新增窗口没有技能可选：** 先进入“技能管理”添加并启用技能。
- **Excel 中文乱码：** 使用应用导出的 CSV；它带 UTF-8 BOM。
- **数据库被占用：** 关闭其他直接打开 `efootball.db` 的工具后重试；应用已设置 5 秒 busy timeout。
- **程序无法启动：** 查看 `%LOCALAPPDATA%\EFootballSkillManager\logs\app.log`。
- **禁用技能还能在旧记录中看到：** 这是预期行为；禁用只阻止新记录默认选择，不破坏历史关联。

## 项目结构

`app/db` 负责连接、迁移和参数化 SQL；`app/services` 负责业务规则、统计、导入导出及备份；`app/ui` 负责桌面界面；`tests` 覆盖核心逻辑。时间以带本地时区偏移的 ISO 8601 字符串保存。

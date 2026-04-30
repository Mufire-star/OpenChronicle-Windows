# OpenChronicle Windows 使用说明

这份文档针对 `OpenChronicle-Windows` 目录。

## 1. 环境要求

- Windows 11
- PowerShell
- Python 3.11+
- `uv`

如果还没装 `uv`，先参考官方说明安装：

- https://docs.astral.sh/uv/

## 2. 安装

在仓库根目录进入 Windows 版本子目录：

```powershell
cd OpenChronicle-Windows
```

开发环境安装：

```powershell
uv sync --all-extras
```

全局安装命令行工具：

```powershell
powershell -ExecutionPolicy Bypass -File .\install_windows.ps1
```

## 3. 启动

前台启动，便于观察日志：

```powershell
uv run openchronicle start --foreground
```

后台启动：

```powershell
uv run openchronicle start
```

查看状态：

```powershell
uv run openchronicle status
```

停止：

```powershell
uv run openchronicle stop
```

暂停/恢复采集：

```powershell
uv run openchronicle pause
uv run openchronicle resume
```

## 4. 首次检查

先做一次单次采集，确认 UI Automation 和截图链路工作正常：

```powershell
uv run openchronicle capture-once
```

如果成功，会在默认数据目录生成一条捕获记录。

默认数据目录：

```text
%USERPROFILE%\.openchronicle
```

其中常用内容：

- `capture-buffer\`：原始捕获
- `memory\`：生成的 Markdown 记忆
- `logs\`：运行日志
- `index.db`：本地索引库
- `config.toml`：配置文件

## 5. 常用命令

构建时间线块：

```powershell
uv run openchronicle timeline tick
uv run openchronicle timeline list
```

手动触发 writer：

```powershell
uv run openchronicle writer run
```

重建索引：

```powershell
uv run openchronicle rebuild-index
uv run openchronicle rebuild-captures-index
```

查看当前配置：

```powershell
uv run openchronicle config
```

## 6. 接入 Codex / MCP

先确保守护进程已经启动：

```powershell
uv run openchronicle start
```

然后注册到 Codex：

```powershell
uv run openchronicle install codex
```

本地 MCP 地址默认是：

```text
http://127.0.0.1:8742/mcp
```

也可以生成通用 MCP 配置：

```powershell
uv run openchronicle install mcp-json --http
```

## 7. Windows 版本当前行为

- 已支持后台启动/停止
- 已支持前台窗口轮询 watcher
- 已支持 PowerShell UI Automation 抓取
- 已支持截图、timeline、session、writer、MCP 全链路运行

当前仍然是 best-effort：

- Windows watcher 主要擅长检测前台应用/窗口切换
- 对“窗口内逐字输入变化”的捕捉不如前台窗口切换那样稳定
- 一些 Electron 或提权窗口可能只暴露部分 UIA 结构

## 8. 建议排障顺序

1. 运行 `uv run openchronicle status`
2. 运行 `uv run openchronicle capture-once`
3. 检查 `%USERPROFILE%\.openchronicle\logs\`
4. 检查 `%USERPROFILE%\.openchronicle\capture-buffer\` 是否持续有新文件

如果 `capture-once` 都失败，优先排查 PowerShell、截图权限、目标应用是否暴露 UI Automation 信息。

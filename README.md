<p align="center">
  <img src="assets/logo.png" alt="OpenChronicle" width="600" />
</p>

# OpenChronicle Windows

面向 Windows 的本地优先记忆系统，供具备工具调用能力的 LLM Agent 使用。

当前仓库已经整理为 **Windows-only** 版本，不再保留 macOS / Linux 运行分支。

## 这是什么

OpenChronicle 会在本机持续采集与你当前工作相关的上下文，并整理成几层可检索的数据：

- 原始采集文件：窗口信息、可见文本、UI Automation 树、截图
- timeline：短时间窗口内的活动摘要
- session：更长时间段的工作片段
- memory：写入到 Markdown 的长期记忆
- MCP 服务：供 Codex、Claude、opencode 等客户端读取

它的目标不是替代聊天记录，而是给 Agent 一个可查询的“本地个人记忆层”。

## Windows 版包含什么

- 基于 Windows UI Automation 的前台窗口采集
- 基于前台窗口轮询的 watcher
- 截图采集
- timeline 聚合
- session 切分
- reducer / classifier 写入记忆
- MCP 服务

## 环境要求

- Windows 11
- PowerShell
- Python 3.11+
- `uv`

## 安装

进入项目目录后执行：

```powershell
cd OpenChronicle-Windows
uv sync --all-extras
```

如果你希望把 `openchronicle` 安装成全局命令，也可以执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\install_windows.ps1
```

## 使用方式

下面按“第一次使用”的顺序来。

### 1. 安装依赖

```powershell
cd D:\Projects\github_project\OpenChronicle-Windows
uv sync --all-extras
```

说明：

- 不需要手动激活 `.venv`
- 直接使用 `uv run ...` 即可

### 2. 先做一次单次采集测试

```powershell
uv run openchronicle capture-once
```

如果成功，会写入一个采集文件到：

```text
%USERPROFILE%\.openchronicle\capture-buffer\
```

这一步的作用是先确认：

- PowerShell 可调用
- Windows UI Automation 可用
- 截图链路可用

### 3. 启动后台服务

```powershell
uv run openchronicle start
```

如果你想在当前终端里直接看日志，可以用前台模式：

```powershell
uv run openchronicle start --foreground
```

### 4. 查看运行状态

```powershell
uv run openchronicle status
```

这个命令会显示：

- 守护进程是否在运行
- 最近一次采集
- capture buffer 数量
- timeline / session / memory 状态
- MCP / 模型探活状态

### 5. 暂停、恢复、停止

暂停采集：

```powershell
uv run openchronicle pause
```

恢复采集：

```powershell
uv run openchronicle resume
```

停止服务：

```powershell
uv run openchronicle stop
```

## 接入 Codex

这部分也按顺序来。

### 1. 先确保 OpenChronicle 已经启动

```powershell
uv run openchronicle start
```

### 2. 把 OpenChronicle 注册到 Codex 的 MCP 配置

```powershell
uv run openchronicle install codex
```

默认会注册这个本地 MCP 地址：

```text
http://127.0.0.1:8742/mcp
```

这个命令本质上是在调用：

```text
codex mcp add openchronicle --url http://127.0.0.1:8742/mcp
```

### 3. 验证是否注册成功

可以再次检查 OpenChronicle 状态：

```powershell
uv run openchronicle status
```

也可以检查 Codex 的 MCP 配置中是否已有 `openchronicle`。

### 4. 在 Codex 中使用

接入完成后，Codex 就可以把 OpenChronicle 当作一个 MCP 工具源来调用。

典型场景：

- “我刚才在看什么？”
- “帮我找一下今天下午浏览过的某个报错”
- “我最近在做哪个项目？”
- “把最近几分钟的上下文总结一下”

如果你想生成通用 MCP 配置文件，也可以执行：

```powershell
uv run openchronicle install mcp-json --http
```

## 接入 Codex 之后会发生什么

会有变化，但不是“Codex 自动读取你所有本地数据”。

更准确地说，接入之后会发生这几件事：

1. Codex 多了一个可调用的 MCP 服务：`openchronicle`
2. 当 Codex 判断当前问题和你的本地记忆、最近活动、屏幕上下文有关时，它可以调用这些工具
3. 查询结果来自你本机的 OpenChronicle 数据目录，而不是 Codex 自己凭空记忆

也就是说：

- **接入前**：Codex 只能靠当前对话和你主动贴出来的内容回答
- **接入后**：Codex 可以额外查询 OpenChronicle 的本地记忆和最近采集结果

## 接入 Codex 之后，Codex 可以调用吗

可以，但要分清楚“可以调用什么”。

接入后，Codex 可以调用的是 OpenChronicle 暴露出来的 **只读 MCP 工具**，例如：

- 读取 memory
- 搜索 memory
- 搜索 raw captures
- 读取最近一次上下文
- 读取某个时间点附近的 capture

它不会因为接入 MCP 就自动获得这些能力之外的权限。

当前这条链路的关键点是：

- OpenChronicle 负责采集、存储、索引
- Codex 负责在合适的时候发起查询
- MCP 只是两者之间的工具协议

## 接入 Codex 之后，和没接入相比有什么变化

最实际的变化是下面这些：

- Codex 能回答“你最近在做什么”这类问题
- Codex 能从本地记忆中找人名、项目名、时间线
- Codex 能查询最近采集到的屏幕内容，而不只看当前聊天窗口
- 你不需要每次都手动把上下文粘贴进对话

但也有两个边界：

- 如果 OpenChronicle 没启动，Codex 调不到这个 MCP 服务
- 如果采集层没有抓到目标应用的内容，Codex 也查不到对应上下文

## 常用命令

单次采集：

```powershell
uv run openchronicle capture-once
```

构建和查看 timeline：

```powershell
uv run openchronicle timeline tick
uv run openchronicle timeline list
```

手动运行 writer：

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

## 默认数据目录

```text
%USERPROFILE%\.openchronicle
```

常见内容：

- `capture-buffer\`：原始采集文件
- `memory\`：Markdown 记忆文件
- `logs\`：运行日志
- `index.db`：SQLite 索引
- `config.toml`：配置文件

## 已知限制

- UI Automation 能拿到多少内容，取决于目标应用暴露出来的信息
- 一些 Electron 应用的结构较浅，文本不一定完整
- 提权窗口、受保护窗口可能拿不到完整内容
- 相比“窗口切换”，逐字输入变化的捕捉稳定性会弱一些

## 文档

- [docs/windows-usage.md](docs/windows-usage.md)
- [docs/windows.md](docs/windows.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/config.md](docs/config.md)
- [docs/capture.md](docs/capture.md)
- [docs/timeline.md](docs/timeline.md)
- [docs/session.md](docs/session.md)
- [docs/writer.md](docs/writer.md)
- [docs/mcp.md](docs/mcp.md)
- [docs/memory-format.md](docs/memory-format.md)
- [docs/troubleshooting.md](docs/troubleshooting.md)

## 开发

运行测试：

```powershell
uv run pytest -p no:cacheprovider
```

静态检查：

```powershell
uv run ruff check
```

## 许可证

MIT

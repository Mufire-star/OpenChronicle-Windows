<p align="center">
  <img src="assets/logo.png" alt="OpenChronicle" width="600" />
</p>

<h1 align="center">OpenChronicle Windows</h1>

<p align="center">
  面向 Windows 的本地优先屏幕上下文记忆系统，为 LLM Agent 提供可查询的工作记忆层。
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> ·
  <a href="#接入-llm-客户端">接入 LLM 客户端</a> ·
  <a href="#架构概览">架构概览</a> ·
  <a href="#文档">文档</a> ·
  <a href="#开发">开发</a>
</p>

---

## 为什么做这个项目

[OpenChronicle](https://github.com/OpenChronicle) 是一个很棒的本地屏幕记忆系统，但原项目**只支持 macOS**。

日常开发中，我大部分时间在 Windows 上工作，并不使用MAC。于是我把 OpenChronicle 的核心思路移植到了 Windows 平台，利用 **Windows UI Automation** 替代 macOS 的 Accessibility API，同时保留了原项目的数据流水线设计（capture → timeline → session → memory → MCP）。

**如果你也觉得 OpenChronicle 的理念很好，但苦于只能在 Mac 上用，这个Windows版本也许就是为你准备的。**

## 这是什么

OpenChronicle Windows 会在本机持续采集你当前工作相关的上下文，整理成多层可检索的数据，通过 MCP 协议暴露给 LLM 客户端：

| 层级     | 说明                                       |
| -------- | ------------------------------------------ |
| 原始采集 | 窗口信息、可见文本、UI Automation 树、截图 |
| Timeline | 短时间窗口内的活动摘要                     |
| Session  | 更长时间段的工作片段                       |
| Memory   | 写入 Markdown 的长期记忆                   |
| MCP 服务 | 供 Codex、Claude、opencode 等客户端读取    |

它的目标不是替代聊天记录，而是给 Agent 一个可查询的**本地个人记忆层**。

## 快速开始

### 环境要求

- Windows 11
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

### 安装

```powershell
git clone https://github.com/Mufire-star/OpenChronicle-Windows.git
cd OpenChronicle-Windows
uv sync --all-extras
```

全局安装（可选）：

```powershell
powershell -ExecutionPolicy Bypass -File .\install_windows.ps1
```

### 验证采集链路

```powershell
uv run openchronicle capture-once
```

成功后会写入采集文件到 `%USERPROFILE%\.openchronicle\capture-buffer\`。

### 启动服务

```powershell
# 后台运行
uv run openchronicle start

# 前台运行（可查看日志）
uv run openchronicle start --foreground
```

### 查看状态

```powershell
uv run openchronicle status
```

### 暂停 / 恢复 / 停止

```powershell
uv run openchronicle pause
uv run openchronicle resume
uv run openchronicle stop
```

## 接入 LLM 客户端

### Codex

```powershell
# 确保 OpenChronicle 已启动
uv run openchronicle start

# 注册 MCP 服务
uv run openchronicle install codex
```

默认注册地址：`http://127.0.0.1:8742/mcp`

如果你想直接使用 Codex CLI 的原生命令，也可以等价注册：

```powershell
codex mcp add openchronicle --url http://127.0.0.1:8742/mcp
codex mcp list
```

如果 Codex 已经在运行，注册后可能需要重启 Codex 或重新打开会话，新的 MCP 工具才会出现在当前会话里。

### 其他客户端（Claude、opencode 等）

生成通用 MCP 配置文件：

```powershell
uv run openchronicle install mcp-json --http
```

### 接入后能做什么

接入前，LLM 只能靠当前对话上下文回答；接入后，它可以额外查询 OpenChronicle 的本地记忆和屏幕采集结果：

- "我刚才在看什么？"
- "帮我找一下今天下午浏览过的某个报错"
- "我最近在做哪个项目？"
- "把最近几分钟的上下文总结一下"

所有查询都是**只读**的，LLM 只能调用 OpenChronicle 暴露的 MCP 工具，不会获得其他权限。

## 架构概览

```
┌─────────────────────────────────────────────────┐
│                 Windows 桌面                      │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │ 窗口 A    │  │ 窗口 B    │  │ 窗口 C    │    │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘    │
│        └──────────────┼──────────────┘           │
│                       ▼                           │
│            ┌──────────────────┐                   │
│            │   UI Automation  │ ← 截图 + 文本采集  │
│            └────────┬─────────┘                   │
│                     ▼                             │
│  ┌──────────────────────────────────────────┐    │
│  │            Pipeline                       │    │
│  │  capture → timeline → session → memory    │    │
│  │                    ↕                       │    │
│  │              LLM Writer                    │    │
│  └──────────────────┬───────────────────────┘    │
│                     ▼                             │
│            ┌──────────────────┐                   │
│            │   MCP Server     │                   │
│            │  :8742/mcp       │                   │
│            └────────┬─────────┘                   │
└─────────────────────┼───────────────────────────┘
                      ▼
         ┌────────────────────────┐
         │   LLM 客户端           │
         │ Codex / Claude / etc.  │
         └────────────────────────┘
```

## 常用命令

| 命令                                          | 说明            |
| --------------------------------------------- | --------------- |
| `uv run openchronicle capture-once`           | 单次采集测试    |
| `uv run openchronicle timeline tick`          | 构建 timeline   |
| `uv run openchronicle timeline list`          | 查看 timeline   |
| `uv run openchronicle writer run`             | 手动运行 writer |
| `uv run openchronicle rebuild-index`          | 重建记忆索引    |
| `uv run openchronicle rebuild-captures-index` | 重建采集索引    |
| `uv run openchronicle config`                 | 查看当前配置    |

## 默认数据目录

```
%USERPROFILE%\.openchronicle
├── capture-buffer\    # 原始采集文件
├── memory\            # Markdown 记忆文件
├── logs\              # 运行日志
├── index.db           # SQLite 索引
└── config.toml        # 配置文件
```

## 已知限制

- UI Automation 能拿到的内容取决于目标应用暴露的信息
- 部分 Electron 应用结构较浅，文本可能不完整
- 提权窗口 / 受保护窗口可能无法采集
- 逐字输入变化的捕捉稳定性弱于窗口切换事件

## 文档

- [架构说明](docs/architecture.md)
- [Windows 使用指南](docs/windows-usage.md)
- [配置说明](docs/config.md)
- [采集层](docs/capture.md)
- [Timeline](docs/timeline.md)
- [Session](docs/session.md)
- [Writer](docs/writer.md)
- [MCP 服务](docs/mcp.md)
- [记忆格式](docs/memory-format.md)
- [故障排查](docs/troubleshooting.md)

## 开发

```powershell
# 运行测试
uv run pytest -p no:cacheprovider

# 静态检查
uv run ruff check
```

## 致谢

- [OpenChronicle](https://github.com/OpenChronicle) — 原项目，提供了核心架构和设计理念

## 许可证

MIT

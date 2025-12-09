# MCP Remote Command Execution Tool — MVP Specification

## 1. Overview

本文件描述一个基于 **FastMCP** 构建、可对接 **Dify** 平台的 MVP 版本远程命令执行工具。该工具封装了已有的远程命令执行服务接口（基于 Ansible + Netmiko），并以标准 MCP Tool 的方式暴露给 LLM 使用，帮助工作流自动执行 RCA（Root Cause Analysis，根因分析）。

工具功能定位于：**允许大模型在设备上远程执行命令（只读账户），以便进行问题排查并生成最终建议。**

---

## 2. MVP 版本范围（Scope）

### 2.1 功能目标
1. 提供一个 **基于 FastMCP 的 MCP 工具服务**。
2. 封装后端已有的远程命令执行接口。
3. 暴露一个极简参数：
   - `command`: `string | Array<string>`
4. 返回结构化数据（JSON），包括：
   - 执行的命令
   - 命令执行结果（stdout、stderr）
   - 底层服务的错误（如果存在）
   - 执行时长等元数据

---

## 3. 架构设计

### 3.1 整体调用链路

1. 告警原始信息 ——> 工作流 LLM
2. LLM 解析告警内容，确定需要进一步排查
3. LLM 调用 MCP 工具：
   ```
   tool: remote_exec.run
   args: { command: "df -h" }
   ```
4. MCP 工具调用内部远程命令执行服务 → 返回结构化结果
5. LLM 分析结果并持续通过 MCP 工具执行进一步命令
6. LLM 最终产出 RCA 总结与建议

---

## 4. MCP 工具设计（FastMCP）

### 4.1 工具名称
`remote_exec`

### 4.2 工具能力
```
run(command: string | string[]): {
  results: [
    {
      command: string,
      stdout: string,
      stderr: string,
      exit_code: number,
      start_time: string,
      end_time: string,
      duration_ms: number
    }
  ],
  error?: {
    message: string,
    detail?: any
  }
}
```

---

## 5. 远程命令执行服务封装

MCP 侧仅作为 HTTP client，将命令转发至已有内部服务。

示例响应结构：

```json
{
  "results": [
    {
      "command": "df -h",
      "stdout": "Filesystem ...",
      "stderr": "",
      "exit_code": 0
    }
  ]
}
```

MCP 在此基础上补充元数据并返回给 LLM。

---

## 6. Agent 系统 Prompt 设计（用于 Dify Agent）

以下为建议的系统 prompt，使 LLM 能够稳定执行 RCA 流程：

---

### **Agent System Prompt（可直接使用）**

你将作为一名自动化运维分析 Agent，负责根据告警信息执行 RCA（Root Cause Analysis）。你可以使用一个名为 **remote_exec** 的 MCP 工具，该工具允许你在目标设备上远程执行命令，并返回结构化结果。

你的目标如下：

1. **理解告警内容**：深入分析输入的原始告警信息，明确影响范围、可能原因、涉及组件。
2. **规划命令执行步骤**：决定需要执行哪些诊断命令以验证假设，例如磁盘、CPU、内存、网络等命令。
3. **调用 remote_exec 工具观察系统状态**：每次执行命令前明确目的；执行后分析返回的 stdout/stderr。
4. **逐步逼近根因**：基于命令执行结果持续收敛思路，必要时多次调用工具。
5. **生成最终 RCA 报告**，包括：
   - 事件背景
   - 问题现象
   - 调查过程（包含执行过的命令与结论）
   - 最终根因
   - 建议的修复步骤（以命令方式提供）
   - 风险提示与后续监控建议

注意事项：
- 尽量使用最少的命令获得最大信息。
- 对返回的结构化结果进行细致分析。
- 命令必须是只读性质，不得对系统产生破坏性影响。

---

## 7. 项目结构（示例）

```
mcp-remote-exec/
├── app.py                # FastMCP 服务入口
├── client.py             # 封装远程执行服务的 HTTP client
├── schemas.py            # Pydantic 数据模型
├── config.py             # 服务配置（URL、超时）
├── README.md
└── requirements.txt
```

---

## 8. 下一步工作（MVP 之后）

1. 加入命令白名单/黑名单
2. 引入上下文缓存，减少重复命令
3. 增强错误处理与重试逻辑
4. 支持多设备/多账号切换
5. 引入 Streaming 返回（用于长时间命令）

---

## 9. 结语

该 MVP 方案保持极简设计，专注于验证核心链路：
**告警 → LLM 分析 → 远程执行命令 → RCA 结果**

Dify / FastMCP / 现有远程命令执行服务之间的组合能够快速形成一个具备实战价值的自动化运维分析流水线。


```toml
[project]
name = "undev-mcp"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
	"fastmcp==2.13.3",
	"httpx>=0.28.1,<0.29",
]

```
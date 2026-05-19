# ADR-0009: MCP Integration

**Status**: Proposed
**Date**: 2026-05-20
**Deciders**: Dylan
**Related**: ADR-0006 (Dual System), ADR-0007 (Confidentiality)

## Context

P4 末计划把 contract review pipeline 包装为 **MCP Server**，让外部 MCP Client 可以调用我们的能力：

- **Claude Code / Cursor** 等开发工具 → 直接在 IDE 里调"审查合同"
- **Chat Agent v2**（P5a 自建）→ 通过 MCP Client 复用 pipeline，不重写逻辑
- **未来其他 MCP-compatible 客户端**

MCP (Model Context Protocol) 是 Anthropic 在 2024 末推出的开放协议，2026 已成为 LLM 工具集成的事实标准。

## Decision Drivers

按优先级：

1. **Reusability**：pipeline 暴露后，chat agent v2 不重写合同审查逻辑
2. **Demo 价值**：在 Claude Code 里直接 `审查这份合同` 是有视觉冲击力的演示
3. **生态适配**：2026 主流 agent 框架都支持 MCP，不加入意味着脱节
4. **维护成本可控**：MCP server 包装层应尽量薄（< 200 行）

## Considered Options

### A. Transport（传输层）

1. **stdio only** — 仅本地 subprocess 通信，简单
2. **HTTP/SSE only** — 仅远程 HTTP+SSE
3. **stdio + HTTP/SSE 双协议** — 本地用 stdio，远程用 HTTP/SSE ⭐

### B. Auth（认证）

1. **无 auth**（仅本地 stdio）— 简单
2. **API Key**（headers / env var）— 业界主流 ⭐
3. **OAuth 2.0** — 复杂，过度
4. **mTLS** — 高安全但部署难

### C. Tool 粒度

1. **单一 tool `review_labor_contract`** — 一站式审查 ⭐
2. **多个细粒度 tool**（per category） — 灵活但客户端复杂

### D. SDK 选型

1. **Anthropic 官方 `mcp` Python SDK** — 标准，社区生态丰富 ⭐
2. **FastMCP** — 第三方，更简洁但学习曲线
3. **自研实现 MCP 协议** — 不必要

### E. 是否提交官方 directory

1. **不提交**（当前决定） — 保持私有，未来再提 ⭐
2. **提交 [MCP server directory](https://github.com/modelcontextprotocol/servers)** — 开源贡献，公开使用

## Decision

**Chosen**:
- **A3** stdio + HTTP/SSE 双协议
- **B2** API Key 认证（仅 HTTP/SSE 启用）
- **C1** 单一 tool `review_labor_contract`
- **D1** Anthropic 官方 `mcp` SDK
- **E1** 当前不提交官方 directory（用户决定，未来可改）

### MCP Server 架构

```mermaid
flowchart LR
    subgraph Clients["MCP Clients"]
        CC[Claude Code<br/>stdio]
        Cur[Cursor<br/>stdio]
        Our[Chat Agent v2<br/>stdio]
        Remote[远程客户端<br/>HTTP/SSE]
    end
    
    subgraph Transport["传输层"]
        Stdio[stdio subprocess]
        HTTPSSE[HTTP + SSE 端点<br/>:6800]
    end
    
    subgraph Auth["认证"]
        NoAuth[无 auth<br/>本地 stdio]
        APIKey[API Key<br/>header X-API-Key]
    end
    
    subgraph Server["MCP Server (mcp_server/)"]
        Schema[Tool: review_labor_contract<br/>+ JSON Schema]
        Wrap[Pipeline 包装层]
    end
    
    subgraph Pipeline["现有 Pipeline (src/)"]
        P[review_labor_contract<br/>(纯函数)]
    end
    
    CC --> Stdio
    Cur --> Stdio
    Our --> Stdio
    Remote --> HTTPSSE
    
    Stdio --> NoAuth
    HTTPSSE --> APIKey
    
    NoAuth --> Schema
    APIKey --> Schema
    
    Schema --> Wrap
    Wrap --> P
    
    style Server fill:#fff3cd
    style Pipeline fill:#cfe2ff
    style Auth fill:#f8d7da
```

### Tool Schema 设计

```python
# mcp_server/server.py
from mcp.server import Server
from mcp.types import Tool

server = Server("legal-contract-agent")

@server.tool(
    name="review_labor_contract",
    description="审查中国劳动合同的违法/不利条款。返回风险列表 + 法条引用 + 修改建议。",
    input_schema={
        "type": "object",
        "properties": {
            "contract_text": {
                "type": "string",
                "description": "完整合同文本（UTF-8 中文）",
            },
            "options": {
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "enum": ["zh", "en"],
                        "default": "zh",
                    },
                    "detail_level": {
                        "type": "string",
                        "enum": ["summary", "full"],
                        "default": "full",
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "限定 taxonomy 类目；不传则全 10 类目",
                    },
                    "redact": {
                        "type": "boolean",
                        "default": True,
                        "description": "送 LLM 前是否脱敏（per ADR-0007）",
                    },
                },
            },
        },
        "required": ["contract_text"],
    },
)
async def review_labor_contract(args: dict) -> dict:
    """调用 pipeline 并格式化输出。"""
    from src.pipeline import run_review
    return run_review(
        text=args["contract_text"],
        **args.get("options", {}),
    )
```

### 部署方式

**本地（stdio）模式**：
```bash
# Claude Code 的 mcp_config.json
{
  "mcpServers": {
    "legal-contract-agent": {
      "command": "python",
      "args": ["-m", "mcp_server.server"]
    }
  }
}
```

**远程（HTTP/SSE）模式**：
```bash
# 启动 server
python -m mcp_server.server --transport http --port 6800 --api-key $SECRET

# 客户端连接
mcp.connect("http://server:6800", api_key="...")
```

### Why this option

- **双 transport** 让本地（stdio）+ 远程（HTTP/SSE）都可用，覆盖所有场景
- **API Key** 是 2026 实务最常用平衡（vs OAuth 过重 / mTLS 复杂）
- **单一 tool** 让客户端调用简单 — 客户不需要知道 10 个类目细节
- **官方 SDK** 跟得上协议演进，避免自研版本落后
- **当前不交 directory** — 用户选择保持私有；未来 P5b 后如效果好可改

### Why not the others

| Option | Reason rejected |
|--------|-----------------|
| A1 stdio only | 远程客户端无法接入 |
| A2 HTTP only | 本地集成 Claude Code 不够丝滑 |
| B1 无 auth | 远程 HTTP 必须有 auth |
| B3 OAuth | 单用户场景过重 |
| C2 多细粒度 tool | 客户端复杂度暴涨，10 个 tool 名各自维护 |
| D2 FastMCP | 第三方，社区相对小 |
| D3 自研 | 重造轮子 |
| E2 立即提交 directory | 用户决定先内部成熟后再提 |

## Implementation Plan

**P4 W14（4 天）**：

| Day | 任务 |
|-----|------|
| D1 | 装 Anthropic `mcp` SDK + 初版 stdio server 骨架 |
| D2 | Tool schema 实现 + pipeline 包装 + 本地 Claude Code 测试 |
| D3 | HTTP/SSE transport + API Key auth |
| D4 | 端到端 demo 录制 + 文档 `mcp_server/README.md` |

**注意**：MCP server 包装的 pipeline 应该是 P4 W13 之前已经 stable 的版本。如果 pipeline 还在改，MCP 包装一定要在 pipeline freeze 之后做。

## Consequences

### Positive

- Pipeline 可被任何 MCP client 复用（demo 价值 + chat agent v2 复用基础）
- 双 transport 让本地开发流畅 + 远程演示也行
- API Key auth 简单可用，未来升级 OAuth 不阻塞当前

### Negative / Accepted Tradeoffs

- MCP 协议本身在演进（2026 仍有 minor 更新），SDK 升级时要测试
- 远程 HTTP/SSE 多一份运维（端口、TLS 终端、API Key 轮转）
- 双 transport 实现 + 测试比单一更复杂（多 1 天工作量）

### Mitigations

- 跟踪 Anthropic MCP SDK release notes，每月一次小版本评估
- HTTP/SSE 默认仅本地 bind（127.0.0.1），生产部署再开公网（需配 nginx + TLS）
- 双 transport 的核心逻辑（tool 实现）共享，仅 transport 层差异 ≤ 50 行

## Confirmation

- **P4 W14 D2**：Claude Code 里 `审查这份合同` 能跑通
- **P4 W14 D3**：远程 HTTP/SSE 测试用 curl 成功
- **P4 W14 D4**：demo 视频录制完成 + 文档发布
- **回头改**：
  - 如 P5a chat agent v2 不能用 MCP 顺畅集成 → 重新评估单 vs 多 tool 粒度
  - 如用户反馈强烈要求公开 → 提交官方 MCP directory

## References

- 内部：[ADR-0006](ADR-0006-dual-system-architecture.md), [ADR-0007](ADR-0007-confidentiality.md)
- 外部：
  - [Model Context Protocol 规范](https://modelcontextprotocol.io)
  - [Anthropic `mcp` Python SDK](https://github.com/modelcontextprotocol/python-sdk)
  - [Official MCP Server Directory](https://github.com/modelcontextprotocol/servers)（未来提交）

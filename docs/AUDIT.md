# 审计层 AuditLog —— 所有"留痕"事的统一服务

**Status**: Draft
**Date**: 2026-05-26
**Owner**: Dylan
**读者**: 想知道"出事能不能查""每次调用记了啥""审计文件长啥样"的人
**关联**: [SYSTEM1_PIPELINE.md](SYSTEM1_PIPELINE.md) §9.1（审计挂载原则）、[SECURITY_COMPLIANCE.md](SECURITY_COMPLIANCE.md)、[PRIVACY.md](PRIVACY.md)、[LLM_CLIENT.md](LLM_CLIENT.md)、[adr/ADR-0007](adr/ADR-0007-confidentiality.md)

---

## 用大白话先讲一遍

系统里"该留痕的事"有好几类：调了 LLM、Routing 怎么选的、收了啥文件、隐私守门发现了异常……以前散在各模块各写各的日志，**乱**。这份文档讲的就是：**统一一个"审计层" `AuditLog`**，谁要留痕都用它，**写 / 存 / 轮转 / 保留 / 查询 一个地方包圆**。

- **是什么**：通用、本地、append-only、按日轮转的 JSONL 写入器。
- **不是什么**：不是 debug 日志（那是 stderr/logger 的事）；不懂业务（只接受 record，不判对错）。

## 它干啥（4 件）

1. **接受记录**：任何模块调 `audit.write(record)` 就追加一条。
2. **存储**：本地 JSONL 文件，按记录类型 + 日期分。
3. **维护**：每天轮转新文件、老的压缩、超过保留期清掉。
4. **查询**：按"哪天、谁调的、什么类型"过滤拉出来看。

**不干**：分析、报警决策（那是上层的事）；判记录对不对（写者负责）。

## 4 类记录（MECE，每类一个"频道"）

| 类型 | 谁写 | 干嘛 |
|------|------|------|
| `LLMCall` | LLMClient | 每次 LLM 调用留痕（合规 + 计费 + 调试） |
| `RoutingDecision` | Routing（②） | 路由决策可复原（[SYSTEM1 §3.3.8](SYSTEM1_PIPELINE.md) 字段定义） |
| `IngestionEvent` | 入料边界 | 收件 / 拒件（合规来源凭证 + 安全） |
| `PrivacyEvent` | PrivacyKeeper | 隐私异常（漏抹告警 / 响应含 PII / RedactionError） |

## 每类记录的字段

### LLMCall（一次 LLM 调用）

| 字段 | 含义 |
|------|------|
| `type` | 固定 `"llm_call"` |
| `timestamp` | ISO 8601 + 时区 |
| `request_id` | 同次 caller 多次重试共用 |
| `caller` | `metadata.fallback` / `detector.probation` / ... |
| `provider` / `model` | 谁、什么模型 |
| `redaction_applied` | **关键合规字段**：必须 true，false 触发告警 |
| `prompt_redacted` / `response_text` | 脱敏后的请求 + LLM 回复（长则截到 4KB） |
| `tokens_in` / `tokens_out` / `cost_yuan` | 用量与成本 |
| `latency_ms` | 耗时 |
| `status` / `error` / `retry_count` | ok/retry/error；错误信息；重试几次 |

例子：
```json
{"type":"llm_call","timestamp":"2026-06-15T14:23:11+08:00","request_id":"req_a8f3","caller":"metadata.fallback","provider":"deepseek","model":"deepseek-v3","redaction_applied":true,"prompt_redacted":"...乙方：[姓名_1]...","response_text":"{\"position\":\"软件工程师\"}","tokens_in":312,"tokens_out":18,"cost_yuan":0.003,"latency_ms":1182,"status":"ok","error":null,"retry_count":0}
```

### RoutingDecision（一次路由决策）

`type="routing_decision"`，其余字段见 [SYSTEM1 §3.3.8](SYSTEM1_PIPELINE.md)：`inputs / chosen_action / chosen_steps / alternatives / overall_confidence / timing_ms`。

### IngestionEvent（一份文件进 / 拒）

| 字段 | 含义 | 例子 |
|------|------|------|
| `type` | `"ingestion_event"` | — |
| `timestamp` | ISO 8601 | — |
| `document_id` | 文档内部 id | `doc_2026_0612_001` |
| `doc_hash` | SHA-256（防篡改/去重） | `a3f8...` |
| `size_bytes` | 文件大小 | 412384 |
| `claimed_format` / `detected_format` | 扩展名 vs 真身 | `.pdf` vs `image` |
| `action` | `accepted` / `rejected` | accepted |
| `reject_reason` | 拒因 | `encrypted` / `not_a_labor_contract` |
| `source` | 上传渠道 | `web` / `cli` / `mcp` |

### PrivacyEvent（隐私异常）

| 字段 | 含义 |
|------|------|
| `type` | `"privacy_event"` |
| `timestamp` | — |
| `severity` | `high`（如 RedactionError）/ `medium`（响应含 PII）/ `low`（疑似漏抹但已 sanity 兜回） |
| `what` | 简短描述 |
| `context_ref` | 关联的 `LLMCall.request_id` 或 `document_id` |

例子：
```json
{"type":"privacy_event","timestamp":"2026-06-15T14:24:02+08:00","severity":"high","what":"sanity scan detected un-redacted ID in prompt","context_ref":"req_b9e1"}
```

## 文件布局

```
data/audit/
├── llm_calls/         2026-06-15.jsonl, 2026-06-14.jsonl.gz, ...
├── routing_decisions/ 2026-06-15.jsonl, ...
├── ingestion_events/  2026-06-15.jsonl, ...
├── privacy_events/    2026-06-15.jsonl, ...
└── README.md          字段 schema 速查
```

每类一个目录 + 按日 JSONL + 旧文件 `.gz`。整个 `data/audit/` **加进 `.gitignore`**，不进 git。

## 写入保证

- **追加写**（`open(..., "a")`）：不覆盖、不丢历史。
- **每条 flush + fsync**：性能换合规——崩溃最多丢"正在写一半"的那一条。
- **日轮转**：日期翻一天，开新文件。
- **压缩**：默认 7 天后旧 JSONL 自动 gzip。
- **保留**：默认 90 天，过期自动删（可配；企业合规需要可拉到几年）。

## 查询（不用上重型工具，jq 就够）

```bash
# 今天烧了多少钱
jq -s 'map(.cost_yuan) | add' data/audit/llm_calls/2026-06-15.jsonl

# 按 caller 分组看平均耗时
jq -s 'group_by(.caller) | map({caller: .[0].caller, n: length, avg_ms: (map(.latency_ms) | add / length)})' data/audit/llm_calls/2026-06-15.jsonl

# 找所有 redaction_applied=false 的（应该为空，否则报警）
jq 'select(.redaction_applied == false)' data/audit/llm_calls/*.jsonl

# 今天有没有 high 严重度隐私事件
jq 'select(.severity == "high")' data/audit/privacy_events/2026-06-15.jsonl
```

数据多了再考虑灌进 SQLite 索引；起步阶段 jq 够用。

## API

```python
@dataclass
class AuditRecord:
    type: str
    timestamp: str

@dataclass
class LLMCall(AuditRecord):
    type: str = "llm_call"
    request_id: str = ""
    caller: str = ""
    provider: str = ""
    model: str = ""
    redaction_applied: bool = False
    prompt_redacted: str = ""
    response_text: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost_yuan: float = 0.0
    latency_ms: float = 0.0
    status: Literal["ok", "retry", "error"] = "ok"
    error: str | None = None
    retry_count: int = 0

# RoutingDecision / IngestionEvent / PrivacyEvent 类似，按上面字段表

class AuditLog(Protocol):
    def write(self, record: AuditRecord) -> None: ...
    def query(self, type: str, since: str | None = None,
              until: str | None = None,
              caller: str | None = None) -> Iterator[AuditRecord]: ...
    def rotate(self) -> None: ...               # 日翻天时自动调
    def purge_old(self, keep_days: int = 90) -> None: ...

class JsonlAuditLog(AuditLog):
    """JSONL 按日轮转的实现，append + fsync。"""
```

## 一个例子（串完整流程）

⑥ Metadata 兜底调 LLM 补 `position`：

1. ⑥ 调 `LLMClient.complete(...)`。
2. LLMClient 内部：先调 `PrivacyKeeper.before_llm` 脱敏 → Provider 发请求 → 拿响应 → 调 `PrivacyKeeper.after_llm` 扫响应。
3. **LLMClient 收尾调** `audit.write(LLMCall(caller="metadata.fallback", ..., redaction_applied=True, ...))`。
4. AuditLog 追加这条到 `data/audit/llm_calls/2026-06-15.jsonl` + fsync。
5. 第二天 0:00 翻日，开新文件 `2026-06-16.jsonl`。
6. 第 8 天，老的 `2026-06-15.jsonl` 自动 gzip。
7. 第 91 天，最老的删掉。

**事故复盘**：用户报"6/15 那次审查漏了一个违法点"。运维 `jq` 一捞 `llm_calls/2026-06-15.jsonl` + `routing_decisions/2026-06-15.jsonl`，把当时的 `chosen_steps` + `LLMCall.response_text` 拼起来，能完整复原现场——做对了什么、判错了哪步。

## 边界

- **不存 PII 原文**：`prompt_redacted` 已 PII-free；`response_text` 也是 PrivacyKeeper 扫过的（见 PRIVACY.md L3 + 响应扫）。
- **不混进通用日志**：审计 = 合规级，单独路径；代码 debug 走另一条 logger（stderr / syslog）。
- **不做实时分析**：AuditLog 只写不算。聚合 / 告警是上层的事。
- **多租户**（未来）：路径加 `tenants/<id>/` 前缀，per-tenant 隔离。

## References

- [SYSTEM1 §9.1](SYSTEM1_PIPELINE.md) — 审计挂载原则（哪些模块要审计）
- [SYSTEM1 §3.3.8](SYSTEM1_PIPELINE.md) — RoutingDecision 字段
- [PRIVACY.md](PRIVACY.md) — PrivacyEvent 的产生方
- [LLM_CLIENT.md](LLM_CLIENT.md) — LLMCall 的产生方
- [SECURITY_COMPLIANCE.md](SECURITY_COMPLIANCE.md) — 合规政策
- [adr/ADR-0007](adr/ADR-0007-confidentiality.md) — 保密架构决策

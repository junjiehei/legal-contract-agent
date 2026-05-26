# LLMClient —— LLM 调用的统一门面

**Status**: Draft
**Date**: 2026-05-26
**Owner**: Dylan
**读者**: 要调 LLM 的人（Detector / ⑥ Metadata / Verifier / VlmParser / 未来 Chat Agent）
**关联**: [PRIVACY.md](PRIVACY.md)、[AUDIT.md](AUDIT.md)、[adr/ADR-0001](adr/ADR-0001-llm-selection.md)、[SYSTEM1_PIPELINE.md](SYSTEM1_PIPELINE.md)、[SYSTEM2_CHAT_AGENT.md](SYSTEM2_CHAT_AGENT.md)

---

## 用大白话先讲一遍

系统里好多模块要调 LLM（DeepSeek 判违法、Qwen-VL 认字、Metadata 兜底抽要素…）。如果每家各自打 API，**五件事会全线漏**：PII 泄漏、provider 切不动、5xx 崩、token 烧多少没人知道、单测要花真钱。

所以**所有 LLM 调用收口到一个 LLMClient**——它就是一扇门。门上挂着两个守卫：**[PrivacyKeeper](PRIVACY.md)**（防 PII 漏出）+ **[AuditLog](AUDIT.md)**（记下每次调用）。LLMClient 自己**只管把请求安全稳地送出去、把响应拿回来**。

- **是什么**：薄薄一层 LLM 调用门 + 重试 + provider 切换 + mock。
- **不是什么**：不脱敏（PRIVACY 管）、不写日志（AUDIT 管）、不组 prompt（caller 管）、不做 embedding（另立 `EmbeddingClient`）。

## 为什么要收口（5 条 MECE）

| 漏点 | 不收口会怎样 |
|------|-------------|
| **安全** | PII 脱敏靠每个调用方自觉 → 早晚漏（详见 PRIVACY.md） |
| **可换** | DeepSeek 换 Claude/Ollama 要改 N 处 |
| **稳定** | 重试/限流/超时各家各写 |
| **可观测** | 每次烧了多少 token/钱、出错没现场（详见 AUDIT.md） |
| **可测** | 单测/eval 不能真打 API |

## 范围与边界

| 进 LLMClient | 不进 |
|--------------|------|
| 文本 LLM（DeepSeek V3/R1） | Embedding（另立 `EmbeddingClient`） |
| 视觉 LLM（Qwen-VL），同一接口 | RAG 检索拼 context（RAG 的事） |
| Provider 切换（DeepSeek / Qwen / Ollama / Mock） | Prompt 模板（caller 的事） |
| 重试 / 退避 / 超时 | agent loop（Chat Agent 的事） |
| 流式 + tool_use（**P5a 实现**，P2 留口） | |

## 通信契约（caller ↔ client）

### `Message` / `ContentPart` —— OpenAI 风格消息

| 字段 | 含义 |
|------|------|
| `role` | `system` / `user` / `assistant` / `tool`（"tool" P5a 用） |
| `content` | 纯字符串；或 `list[ContentPart]`（多模态） |

```python
@dataclass
class ContentPart:                        # 多模态时把文本和图拆 part
    type: Literal["text", "image_url"]
    text: str | None = None
    image_url: str | None = None          # 本地路径或 data URL

@dataclass
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[ContentPart]
```

### `LLMOptions` —— 生成参数

| 字段（默认） | 含义 |
|------------|------|
| `temperature = 0.0` | 法律场景求稳 |
| `max_tokens = None` | 生成上限 |
| `json_mode = False` | 强制 JSON 输出 |
| `seed = None` | 复现用 |
| `timeout_s = 30.0` | 超时 |

```python
@dataclass
class LLMOptions:
    temperature: float = 0.0
    max_tokens: int | None = None
    json_mode: bool = False
    seed: int | None = None
    timeout_s: float = 30.0
```

### `LLMRequest` / `LLMResponse`

```python
@dataclass
class LLMRequest:
    messages: list[Message]
    model: str                                # "deepseek-v3" / "deepseek-r1" / "qwen-vl"
    options: LLMOptions = field(default_factory=LLMOptions)
    caller: str = ""                          # "metadata.fallback" / "detector.probation" ...
    tools: list["ToolSpec"] | None = None     # P5a 留口，P2 留空

@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int

@dataclass
class LLMResponse:
    text: str
    finish_reason: Literal["stop", "length", "content_filter", "error"]
    usage: TokenUsage
    model_used: str
    provider: str
    latency_ms: float
    raw_id: str | None = None
    tool_calls: list["ToolCall"] | None = None   # P5a 留口，P2 留空
```

## Provider 适配（每厂一个）

```python
class Provider(Protocol):
    name: str                                 # "deepseek" / "qwen-vl" / "mock" / "ollama" ...
    def supports_vision(self) -> bool: ...
    def call(self, request: LLMRequest) -> LLMResponse: ...
```

**P2 必备**：`DeepSeekProvider`（V3 + R1）+ `QwenVLProvider` + `MockProvider`。
**之后**：`OllamaProvider`（私有部署）、其他厂家。

加新厂家 = 加新适配器，主体不动。

## 重试 / 退避 / 超时

```python
@dataclass
class RetryPolicy:
    max_retries: int = 3
    backoff_base_s: float = 1.0           # 1s, 2s, 4s 指数退避
    retry_on: tuple = ("429", "5xx", "timeout")
```

5xx / 429 / 超时 → 指数退避重试；4xx 非 429 → 立刻抛错不重试。

## LLMClient 主类（瘦）

```python
class LLMClient:
    def __init__(
        self,
        providers: dict[str, Provider],       # model_name -> Provider
        retry_policy: RetryPolicy,
        privacy: "PrivacyKeeper",             # 唯一脱敏入口
        audit: "AuditLog",                    # 唯一审计入口
    ): ...

    def complete(self, messages, model, options=None, caller="") -> LLMResponse:
        """流程：
           1) privacy.before_llm(messages, caller) → safe_messages  （可能抛 RedactionError）
           2) retry-loop: provider.call(LLMRequest(safe_messages, ...))
           3) privacy.after_llm(response, caller) → 可能二次抹
           4) audit.write(LLMCall(...))
           5) return response
        """

    def complete_stream(self, messages, model, options=None, caller="") -> Iterator["ResponseChunk"]:
        """P5a 实现，P2 仅签名占位。"""
```

视觉调用同 `complete()`——messages 里塞 `ContentPart(type=image_url)`，`Provider.supports_vision()` 决定能不能跑。

## 一个例子（端到端）

⑥ Metadata 兜底补 `position`：

```python
# 流水线开始处一次性初始化
audit = JsonlAuditLog(path="data/audit")
privacy = PrivacyKeeper(audit_log=audit)
client = LLMClient(
    providers={"deepseek-v3": DeepSeekProvider(...), "mock": MockProvider(...)},
    retry_policy=RetryPolicy(),
    privacy=privacy,
    audit=audit,
)

# ⑥ 规则层抽出名字
md_rules = extract_rules(ast)
privacy.set_session_pii([md_rules.party_b_name])     # 必须在第一次调 LLM 之前

# 现在可以调 LLM 了
msgs = [
    Message(role="system", content="抽出岗位名称，JSON 输出"),
    Message(role="user", content="...乙方：张三 第二条 乙方担任「软件工程师」..."),
]
resp = client.complete(msgs, model="deepseek-v3",
                       options=LLMOptions(json_mode=True),
                       caller="metadata.fallback")
# resp.text = '{"position": "软件工程师"}'
```

LLMClient 内部干的事：
1. `privacy.before_llm` → 把"张三"换成"[姓名_1]"，sanity 扫，没漏。
2. `DeepSeekProvider.call` → 发请求，遇 429 退避 1s/2s/4s。
3. `privacy.after_llm` → 扫响应，没 PII。
4. `audit.write(LLMCall(caller="metadata.fallback", tokens_in=312, ..., redaction_applied=true, status="ok"))`
5. 返回响应。

**caller 完全不操心**脱敏、重试、记账、provider 切换。

## 测试时

```python
mock_client = LLMClient(
    providers={"deepseek-v3": MockProvider(canned={"position": "测试岗位"})},
    retry_policy=RetryPolicy(max_retries=0),
    privacy=MockPrivacyKeeper(),                # noop redact
    audit=InMemoryAuditLog(),
)
```

200 条 eval 跑不烧钱、不被限流、结果稳定可重复。

## P5a 预留口（流式 + 工具调用）

P2 阶段不实现，**接口已对齐**避免日后重构：

| 留口 | 现在 | P5a 实现 |
|------|------|---------|
| `Message.role = "tool"` | 已定义 | 用于工具返回结果回填 |
| `LLMRequest.tools` | 留空 | 注册可调工具的 schema |
| `LLMResponse.tool_calls` | 留空 | LLM 决定调哪个工具 |
| `LLMClient.complete_stream(...)` | 签名占位 | 真做流式 |

> 注：若 P5a 选 Anthropic Agent SDK（SYSTEM2 Open Question #1），SDK 会绕开 LLMClient 自己调 API——意味着脱敏 / 审计 / DeepSeek 都接不上。届时需重新评估。**当前 LLMClient 设计不被这个选择卡住**（接口都按业界标准来）。

## 边界

- **不写日志**：调 [AUDIT.md](AUDIT.md)（写 `LLMCall`）。
- **不脱敏**：调 [PRIVACY.md](PRIVACY.md)（`before_llm` / `after_llm`）。
- **不组 prompt**：caller 的事。
- **不做 embedding**：另立 `EmbeddingClient`（向量是不同的事）。
- **不调度 agent loop**：那是 Chat Agent / Detector / Verifier 的事。

## References

- [adr/ADR-0001](adr/ADR-0001-llm-selection.md) — LLM 选型决策
- [PRIVACY.md](PRIVACY.md) — 隐私守门（4 类失败 + 5 层防御）
- [AUDIT.md](AUDIT.md) — 审计层（4 类记录）
- [SYSTEM1 §5](SYSTEM1_PIPELINE.md) — Detector 用 LLMClient
- [SYSTEM1 §3.7](SYSTEM1_PIPELINE.md) — ⑥ Metadata 用 LLMClient（PII 时序见 PRIVACY）
- [SYSTEM2_CHAT_AGENT.md](SYSTEM2_CHAT_AGENT.md) — P5a Chat Agent 用同一个 LLMClient

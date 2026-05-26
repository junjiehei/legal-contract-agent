# 隐私守门 PrivacyKeeper —— 所有 PII 防护的统一主人

**Status**: Draft
**Date**: 2026-05-26
**Owner**: Dylan
**读者**: 想知道"姓名身份证怎么不漏""脱敏出错怎么办""哪些字段会被抹"的人
**关联**: [SECURITY_COMPLIANCE.md](SECURITY_COMPLIANCE.md)、[adr/ADR-0007](adr/ADR-0007-confidentiality.md)、[AUDIT.md](AUDIT.md)、[LLM_CLIENT.md](LLM_CLIENT.md)、[SYSTEM1_PIPELINE.md](SYSTEM1_PIPELINE.md) §3.7

---

## 用大白话先讲一遍

合同里有姓名、身份证、手机号、银行卡——这些是 PII（个人身份信息），按法律不能随便给第三方（包括大模型 API）。这份文档讲的就是：**统一一个"隐私守门" `PrivacyKeeper`**，所有跟 PII 相关的事都归它管，**别人（LLMClient、Detector、⑥ Metadata、未来 Chat Agent…）只调它的接口**。

- **是什么**：识别 + 抹换 + 还原 + 核查 + 失败处理的统一模块。
- **不是什么**：不写日志（调 [AUDIT.md](AUDIT.md)）、不调 LLM（[LLM_CLIENT.md](LLM_CLIENT.md) 的事）、不组 prompt（caller 的事）。

## 它干啥（5 件）

1. **识别**：扫一段文本，找出 PII 在哪。
2. **抹换**：把 PII 替换成占位符（`[姓名_1]`），并记下映射。
3. **还原**：必要时把占位符换回原文（多数 caller 不需要）。
4. **核查**：脱敏后再扫一遍（漏没漏）；LLM 响应也扫（是否冒出新 PII）。
5. **失败处理**：发现漏 / 错 / 漏设词表 → 抛错 + 告警 + fail closed。

## 哪些算 PII（识别规则）

| 类别 | 怎么识别 | 占位符 |
|------|----------|--------|
| **姓名**（劳动者、法定代表人） | **已知词表**：⑥ Metadata 抽出的名字（规则层抽出，不用 LLM） | `[姓名_N]` |
| **身份证号** | 正则 `\b\d{17}[\dXx]\b`（18 位、末位可 X）+ 校验码 | `[身份证号_N]` |
| **手机号** | 正则 `\b1[3-9]\d{9}\b` | `[手机号_N]` |
| **银行卡号** | 正则 `\b\d{16,19}\b` + **上下文限定**（前有"卡号/账号/银行"）+ Luhn 校验，三个都中才认 | `[卡号_N]` |
| **邮箱** | 标准 email 正则 | `[邮箱_N]` |
| **住址** | 保守：省/市/区 + 路/街/号 + 省市词典 | `[住址_N]` |

**不抹的（重要！）**：
- **工资数额、日期、合同期限**——是法律事实，检测要用，不能抹。
- **公司名**——不是 PII（机构信息）；客户特别要求保密的，走"商密"另立流程，不在主流程。
- **岗位、城市/区**（粗粒度）——非身份。

**口诀**：**抹"身份"，留"事实"。**

## 占位符规则（同人同号）

一份合同里：第一次见"张三" → `[姓名_1]`，**后面所有"张三"都换成同一个 `[姓名_1]`**（一致性帮 LLM 理解上下文）；不同人"李四" → `[姓名_2]`。映射表 `{[姓名_1]:"张三"}` **只留本地**。

## 命中顺序（先做容易出错的）

1. **词表（已知姓名）**：长名优先，避免子串错配。
2. **长正则**（ID 18 位）：先于卡号 16-19 位，免被吞。
3. **短正则**（手机 11 位、邮箱）。
4. **住址**（最保守）。

## 时序：什么时候设词表

⑥ Metadata 的**规则层**先抽出 `party_b_name` 等（不用 LLM），**然后**：
```python
privacy.set_session_pii([metadata.party_b_name, metadata.party_a_legal_rep, ...])
```
**之后**所有 LLM 调用才进入。这样保证"姓名词表"早于第一次 LLM 调用就位。

**没设就调 LLM** → 直接抛 `SessionNotInitialized`，拒发（强制开发者意识到 PII 责任）。

## 5 层防御纵深

| 层 | 谁负责 | 干啥 |
|----|--------|------|
| **L1 surface 最小化** | **caller** | detector 判某条款时只送那条 + 必要的少量 metadata，别整篇首部都喂——**没送进去的 PII 永远不会漏** |
| **L2 强制脱敏** | PrivacyKeeper | 入口必经 |
| **L3 送出前 sanity 扫** | PrivacyKeeper | 脱敏后再用同一套规则扫一遍，**还有 → 拒发** |
| **L4 审计强制 `redaction_applied=true`** | LLMClient + AuditLog | 为 false 触发告警；月度扫所有 false 调用 |
| **L5 人工抽检** | 运维 | 每月从 `privacy_events` + `llm_calls` 随机 30 条人工复核 |

**至少漏 4 层才出事。**

## 4 种失败 + 怎么处理

| 失败 | 危害 | 怎么发现 | 处理 |
|------|:----:|----------|------|
| **A 漏抹**（PII 漏给 LLM） | 🔴 严重 | L3 sanity 扫到 18 位 ID / 11 位手机 / 词表里的名字还在 | **抛 `RedactionError`** + 写 `PrivacyEvent(severity=high)` + caller 把整次审查标 `manual_review`、**不出报告** |
| **B 过抹**（误抹非 PII） | 🟡 质量降 | 替换比例异常高 → 警示 | 不阻断，降置信 + 记 `PrivacyEvent(severity=low)` |
| **C 还原失败** | 🟢 轻 | restore 找不到映射 | 文本不动 + warning |
| **D LLM 响应冒出真 PII** | 🟡 中 | 对响应跑同一套 PII 检测 | **二次 redact 再给 caller** + 记 `PrivacyEvent(severity=medium)` |

## fail-safe 默认

- **必须显式 `set_session_pii(names)`**，哪怕传 `[]`；没设拒调用。
- **超长文本拒发**（>10K 字符要求 caller 拆段）——超长正则易漏 + 成本爆炸。
- **`MockPrivacyKeeper`** 用于测试（noop redact + 内存 audit，接口同）。

## 改进闭环

- **专门的 redaction 测试集**：手造一份"含各类 PII 的 fixture + 期望脱敏结果"，CI 跑回归。
- **每月 audit 抽样**：从 `privacy_events` + `llm_calls` 随机 30 条人工复核，记"漏抹 / 错抹"比例。
- **发现新漏点 → 加规则 + 补测试集**，不只是临时打补丁。

## API

```python
class RedactionError(Exception):
    """脱敏漏抹 / sanity 失败时抛；caller 必须 catch 并降级为 manual_review。"""

class SessionNotInitialized(Exception):
    """会话未设词表就调 LLM 时抛。"""

@dataclass
class RedactionMap:
    placeholders: dict[str, str]          # "[姓名_1]" → "张三"，仅本地

class PrivacyKeeper:
    def __init__(self, audit_log: "AuditLog"):
        """构造时持有 AuditLog 引用，用于写 PrivacyEvent。"""

    # —— 会话词表 ——
    def set_session_pii(self, names: list[str]) -> None: ...
    def clear_session(self) -> None: ...

    # —— LLMClient 主要调这两个 ——
    def before_llm(self, messages: list["Message"], caller: str) -> list["Message"]:
        """1) 抹 PII；2) 送出前 sanity 扫；3) 漏则抛 RedactionError + 写 PrivacyEvent。"""

    def after_llm(self, response: "LLMResponse", caller: str) -> "LLMResponse":
        """4) 扫响应里有无 PII；有则二次 redact + 写 PrivacyEvent。"""

    # —— 必要时还原（多数不需要）——
    def restore(self, text: str, mapping: RedactionMap) -> str: ...
```

## 一个例子

合同里："乙方：张三 身份证 11010519990101XXXX 月工资 8000 元"。

```python
privacy = PrivacyKeeper(audit_log=audit)
privacy.set_session_pii(["张三"])               # ⑥ 规则层抽出后调

# detector 把这条款送 LLM 判
msgs = [Message(role="user", content="乙方：张三 身份证 11010519990101XXXX 月工资 8000 元")]
safe = privacy.before_llm(msgs, caller="detector.probation")
# safe[0].content = "乙方：[姓名_1] 身份证 [身份证号_1] 月工资 8000 元"
# 工资 8000 留着（检测要用），姓名 + 身份证抹了
```

如果脱敏没抹干净（如词表漏了某个名字）：
- **L3 sanity 扫到 → 抛 `RedactionError`**。
- AuditLog 记 `PrivacyEvent(severity=high, what="sanity caught un-redacted name")`。
- caller 收到异常 → 把这次审查标 `manual_review`，**不出报告**。

## 边界

- **不写日志**：所有"留痕"调 AuditLog。
- **不调 LLM**：PrivacyKeeper 只处理文本，不感知 provider。
- **不组 prompt**：caller 的事。
- **不判 PII 严重程度**：什么算 PII 是规则定的，命中就抹，不分轻重缓急。

## References

- [SECURITY_COMPLIANCE.md](SECURITY_COMPLIANCE.md) — PIPL / 合规政策
- [AUDIT.md](AUDIT.md) — PrivacyEvent 落到这里
- [LLM_CLIENT.md](LLM_CLIENT.md) — 怎么用 `before_llm` / `after_llm`
- [adr/ADR-0007](adr/ADR-0007-confidentiality.md) — 保密架构决策
- [SYSTEM1 §3.7](SYSTEM1_PIPELINE.md) — ⑥ Metadata 何时调 `set_session_pii`

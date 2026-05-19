# 免责声明 / Disclaimer

> 中文在前、English follows

## 中文

### 本工具的性质

本项目（`legal-contract-agent`）是一个**研究性、研究级**的 AI 系统，用于演示**中国劳动合同自动审查**的技术架构。**不构成法律意见**，**不能替代执业律师的专业咨询**。

### 使用本工具时请知悉

1. **结果可能错**：AI 生成的违法判断、法条引用、修改建议都可能存在错误（hallucination、过期、误用法律解释等）。任何重要法律决策**必须**经持牌律师人工复核。

2. **法律有时效**：本工具基于截至 2026-05-17 的法律法规版本。中国法律法规会修订，本工具的法律知识不会自动更新。

3. **地域差异**：中国各省市对劳动法律法规可能有不同的实施细则、判决倾向。本工具的判断主要基于国家级法律法规，未充分考虑地方差异。

4. **个案不同**：劳动争议高度依赖具体事实（如证据、协商过程、行业惯例）。同一条款在不同案情下结论可能不同。本工具只看条款文本，不知道你的实际情况。

5. **数据隐私**：当前版本如果通过云端 LLM API（DeepSeek 等）调用，合同内容会发送给该 LLM 服务商。**请勿上传含真实姓名、身份证、银行账号、商业秘密等敏感信息**。

6. **不能用于**：
   - 替代律师为当事人提供法律服务（违反《律师法》）
   - 司法诉讼、仲裁的官方依据
   - 任何商业法律咨询服务的输出
   - 涉及人身安全、刑事责任、重大财产损失的决策

### 如果你是劳动者

- 本工具可作为**自学和初筛工具**（了解合同里有哪些条款可能有问题）
- 重要决策（签字 / 仲裁 / 诉讼）请咨询当地律师
- 各地可拨打 12333（人社部）或 12348（司法部公共法律服务）热线
- 多数地方提供免费法律援助

### 如果你是开发者 / 学习者

本工具可作为：
- 学习 LLM agent 架构、RAG、eval 方法的实例
- 中文法律 NLP 的参考实现
- 研究项目的脚手架

不可作为：
- 商业产品直接上线（需要律师审核 + 合规认证）
- 自动化法律服务（违法）

### 责任限制

本项目的作者及贡献者**不对**使用本工具产生的任何直接或间接损失承担责任，包括但不限于：
- 误信 AI 判断签订/拒签合同的经济损失
- 误信 AI 判断进行/放弃仲裁诉讼的损失
- 因数据泄露产生的损失

使用本工具即视为接受本免责声明。

---

## English

### Nature of This Tool

This project (`legal-contract-agent`) is a **research-grade, research-grade** AI system demonstrating the technical architecture for **automated review of Chinese labor contracts**. It is **NOT legal advice** and **CANNOT replace consultation with a licensed lawyer**.

### Please Note When Using

1. **Outputs may be wrong**: AI-generated violation judgments, law citations, and suggestions may contain errors (hallucination, outdated info, misinterpretation). All material legal decisions **MUST** be reviewed by a licensed lawyer.

2. **Laws change**: This tool is based on Chinese law as of 2026-05-17. Laws are amended; this tool's legal knowledge does not auto-update.

3. **Regional variation**: Chinese provinces and cities may have different implementation rules and judicial tendencies. This tool primarily reflects national-level law.

4. **Cases vary**: Labor disputes depend heavily on facts (evidence, negotiation, industry norms). The same clause may yield different conclusions in different fact patterns. This tool only sees clause text.

5. **Privacy**: When using cloud LLM APIs (e.g., DeepSeek), contract content is sent to that provider. **Do NOT upload real names, ID numbers, bank accounts, or trade secrets.**

6. **Not for**:
   - Replacing lawyers in providing legal services (violation of Chinese Lawyers Law)
   - Official basis for litigation or arbitration
   - Commercial legal consultation outputs
   - Decisions involving personal safety, criminal liability, or major financial loss

### Liability Limitation

The author(s) and contributors of this project assume **NO LIABILITY** for any direct or indirect damages from use of this tool. Using this tool constitutes acceptance of this disclaimer.

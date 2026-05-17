# 法律法规采集清单

> P1-W1 待办清单。完成一项就在 `data/INVENTORY.md` 登记 + 在这里勾上 ✅。

## 国家法律（national/）— P0 必采

- [x] **中华人民共和国劳动合同法** (2012修正)
  - 目标文件：`labor_contract_law_2012.md`
  - 来源：[flk.npc.gov.cn](https://flk.npc.gov.cn)（搜"中华人民共和国劳动合同法"）

- [x] **中华人民共和国劳动法** (2018修正)
  - 目标文件：`labor_law_2018.md`
  - 来源：flk.npc.gov.cn

- [x] **中华人民共和国社会保险法** (2018修正)
  - 目标文件：`social_insurance_law_2018.md`
  - 来源：flk.npc.gov.cn

- [x] **劳动合同法实施条例** (2008)
  - 目标文件：`lc_law_implementation_2008.md`
  - 来源：[中国政府网 gov.cn](https://www.gov.cn)

- [x] **工资支付暂行规定** (1994) — P1
  - 目标文件：`wage_payment_regulation_1994.md`
  - 来源：gov.cn

- [x] **女职工劳动保护特别规定** (2012) — P1
  - 目标文件：`female_workers_protection_2012.md`
  - 来源：gov.cn

## 司法解释（judicial/）— P0

- [x] **最高人民法院关于审理劳动争议案件适用法律若干问题的解释（一）** (2020)
  - 目标文件：`spc_labor_dispute_interpretation_1_2020.md`
  - 来源：[最高法 court.gov.cn](https://www.court.gov.cn)

## 地方法规（local/）— P2，选 4-6 个

- [ ] 北京市劳动合同条例
- [ ] 上海市劳动合同条例
- [ ] 广东省劳动保障监察条例
- [ ] 江苏省劳动合同条例
- [ ] 浙江省劳动合同条例

## 每份 .md 文件的 frontmatter 模板

文件开头必须包含 YAML frontmatter：

```yaml
---
title: 中华人民共和国劳动合同法
revision: 2012修正
publisher: 全国人民代表大会常务委员会
effective_date: 2013-07-01
source_url: https://flk.npc.gov.cn/...
collected_date: 2026-05-17
license: public_domain
---
```

frontmatter 后是法律正文（建议保留 章/条/款 结构）。

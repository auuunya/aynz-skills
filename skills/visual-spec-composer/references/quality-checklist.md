# 质量检查清单

一份高质量 VGS 应满足以下 7 条标准。可作为交付前自检清单。

> **自动化校验**：结构完整性、字段合法性、一致性检查可用 `scripts/validate_vgs.py` 自动化，详见 `vgs-validator.md`。本清单聚焦人工语义质检。

---

## 7 条质量标准

| # | 标准 | 检查方式 |
|---|---|---|
| 1 | **目标清晰** | `task.intent_summary` 能用一句话说清楚这张图是干什么的 |
| 2 | **结构完整** | `task` / `canvas` / `layout` / `style` / `constraints` / `generation_policy` 均已填写 |
| 3 | **层次分明** | Canonical VGS / Human Brief / Render Views 三层各司其职，不混写 |
| 4 | **无自相矛盾** | `must_have` 与 `must_avoid` 无重叠；style 词之间不互相抵消（如"极简"≠"高密度细节"） |
| 5 | **可执行** | 任意 adapter 拿到这份 VGS 都能转出具体模型 prompt，无歧义字段 |
| 6 | **可降阶** | 存在 Compact 或 Minimal Prompt；small_model_mode 下保住主体 + 构图 + 主风格 |
| 7 | **边界诚实** | 不把精确设计成稿伪装成稳态 one-shot 任务；执行限制已显式写入 notes.warnings |

---

## 快速自检

### 人工语义检查
```
□ task.intent_summary 一句话可读，无歧义
□ style 词之间不互相抵消（如"极简"≠"高密度细节"）
□ references 的 ownership 清晰，无角色混淆
□ 如有 brand_constraints，结构化而非散装文字
□ 执行限制已诚实写入 notes.warnings，无虚假承诺
```

### 结构自动化检查
```
□ 必填字段完整：task / canvas / style / constraints / generation_policy
□ blocks 每项都有 id / role / subject
□ canvas.aspect_ratio + composition_mode 已填
□ generation_policy.execution_mode 已填
□ outputs.render_views 已列出交付档位
□ 运行 validate_vgs.py 0 error
```

---

## 降阶质量保底线

当 `small_model_mode: true` 时，以下三项是**不可丢失的最低保底**：

1. 主体（subject）
2. 构图骨架（composition_mode + layout.skeleton）
3. 主风格（style.genre + style.palette）

其余字段（细节修辞、次要参考、复杂过渡）均可压缩或删除。

---

## 四层验收清单

### 第一层：兼容性

| # | 检查项 | 验证方式 | 预期 |
|---|--------|---------|------|
| C1 | 示例在 validator 下无 error | `scripts/validate_vgs.py examples/*.yaml` | 0 error |
| C2 | 扩展字段剥离后在 validator 下无 error | 剥离 metadata/modules/capabilities 后校验 | 0 error |

### 第二层：语义完整性

| # | 检查项 | 验证方式 | 预期 |
|---|--------|---------|------|
| S1 | 单画面示例字段齐全 | 人工 review | task/canvas/layout/blocks/style/constraints/generation_policy/outputs 全有 |
| S2 | 多分块示例 block 数一致 | `layout.block_count == len(blocks)` | 相等 |
| S3 | 图生图示例 reference 有 ownership | 检查每个 reference 的 ownership.fields | 非空 |

### 第三层：字段溯源

| # | 检查项 | 验证方式 | 预期 |
|---|--------|---------|------|
| T1 | provenance 包含 source_intent | 人工检查 metadata.provenance | 与 task.intent_summary 一致 |
| T2 | derivation_chain 有至少一条记录 | 人工检查 | ≥1 step |
| T3 | 字段归属声明覆盖主要竞争字段 | 人工检查 ownership.fields | 覆盖 palette/lighting/subject 等 |

### 第四层：模块化组合

| # | 检查项 | 验证方式 | 预期 |
|---|--------|---------|------|
| M1 | 单体与组装结果等价 | 组装后 diff | 字段一致 |
| M2 | 组装器可正确合并多个模块 | `scripts/assemble_modules.py` | 输出完整 spec |
| M3 | 循环检测有效 | 手造循环 extends 链 | 报错而非死循环 |
| M4 | override 点路径生效 | 检查覆盖结果 | 符合预期 |

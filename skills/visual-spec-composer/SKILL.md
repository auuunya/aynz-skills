---
name: visual-spec-composer
description: 将模糊的图片生成需求访谈、澄清并整理成执行无关的 Visual Generation Spec (VGS) 结构化视觉规格，同时导出 Human Brief 和模型可读 Render Views。适用于海报、KV、封面、概念图、产品图、拼贴图、分镜帧、图生图改造、多参考图整合等场景。
triggers:
  - "帮我整理生图需求"
  - "把 prompt 结构化"
  - "把参考图变成可执行规格"
  - "做一套图像生成 schema / spec / brief"
  - "设计分块构图生图方案"
  - "图片prompt怎么写"
  - "帮我写图片生成的prompt"
not_for:
  - 纯文字生成任务（不涉及图像）
  - 已有完整prompt只需微调的场景
  - 视频/音频生成任务
---

# 视觉规格编排器

本 Skill 产出三层稳定产物，不绑定任何模型或脚本：

1. **Canonical VGS** - 结构化视觉规格 YAML（字段详见 `references/vgs-schema.md`）
2. **Human Brief** - 给用户确认方向的简短摘要
3. **Render Views** - Full / Compact / Minimal 三档投影（规则见 `references/render-views.md`）

## 使用约定

- 工作目录以本 Skill 根目录为准：`./`
- 先读 `SKILL.md`，再按索引按需读取 `references/`；不要一次性展开全部文件
- 若任务是连续画面 / 分镜 / 系列图，转入 `references/storyboard-mode.md`，用 Sequence Wrapper 包一组 VGS

## 工作流程

### Phase 1：需求澄清

| 步骤 | 动作 | 输入 → 输出 | 参考 |
| ---- | ---- | ---------- | ---- |
| 1.1 | 判定 `input_mode`（text / image / mixed）与任务路由（single_frame / multi_block / image_edit / storyboard_sequence） | 用户原始需求 → `input_mode` + `task_type` | `references/interview-tree.md`, `references/storyboard-mode.md` |
| 1.2 | 按访谈树逐轮提问，一次一问，附推荐答案；能从上下文推断的不重复问 | 不完整字段 → 逐轮填充 VGS 字段 | `references/interview-tree.md` |
| 1.3 | 输出 Human Brief 摘要，**等用户确认方向后再继续**；有异议则回到 1.2 | 部分字段 → Human Brief（方向确认） | — |

**⏸ 检查点 A**：用户确认 Human Brief 方向 → 进入 Phase 2；有异议 → 回到 1.2 修订。

### Phase 2：规格生成

| 步骤 | 动作 | 输入 → 输出 | 参考 |
| ---- | ---- | ---------- | ---- |
| 2.1 | 单帧任务填写 Canonical VGS；多帧任务先定 Sequence Wrapper 再逐帧填写 | 确认方向 → Canonical VGS YAML | `references/vgs-schema.md`, `references/storyboard-mode.md` |
| 2.2 | 对每个 reference 声明 ownership；冲突显式写入 conflict note | 多参考图 → `reference_priority` + `conflict_notes` | — |
| 2.3 | 评估复杂度，选 one_shot / two_stage / multi_pass / brief_only；**验证降阶策略可行性** | VGS → `execution_mode` + `fallback_strategy` | `references/vgs-schema.md §6` |

**⏸ 检查点 B**：必填字段完整性检查（`task` / `canvas` / `layout` / `style` / `constraints`） → 进入 Phase 3。

### Phase 3：校验与交付

| 步骤 | 动作 | 输入 → 输出 | 参考 |
| ---- | ---- | ---------- | ---- |
| 3.1 | 运行校验：运行 `scripts/validate_vgs.py` 校验 VGS；按需降阶 | VGS → 校验报告 + 降阶建议 | `scripts/validate_vgs.py` |
| 3.2 | 自检质量清单；依次交付 Human Brief → Canonical VGS → Render Views | VGS → Full / Compact / Minimal Render Views | `references/quality-checklist.md` |
| 3.3 | 若用户未指定保存位置，默认输出到 `.vgs-output/{theme-name}/` | 文件保存确认 | — |

## 关键决策规则

- 单主体 → `single_frame`；多区拼贴 → `multi_block`；保主体改场景 → `image_edit`
- 连续画面 / 分镜 / 系列图 → 进入 storyboard 编排层；每帧仍使用单帧 VGS
- 多 reference 必须指定 ownership；style ≠ subject
- `block_count > 4` → 优先 `two_stage`；`> 6` → 禁止 `one_shot`
- 小模型模式：Compact Prompt，风格词收敛 ≤ 1 主词
- **诚实边界**：无法稳定执行时，显式说明限制并索引 `references/failure-modes.md`；不伪装成稳态任务
- **语言约定**：若用户未指定产出内容语言，Human Brief / VGS 描述字段 / Render Views 均默认使用中文；VGS 结构字段名保持英文

## 按需读取索引

| 分类 | 文件 | 何时读取 |
|------|------|---------|
| **核心规则** | `references/vgs-schema.md` | 需要确认字段定义、复杂度分级、降阶规则时 |
| | `references/interview-tree.md` | Phase 1 访谈阶段，按问题树逐轮提问时 |
| | `references/render-views.md` | Phase 2 生成 Render Views 投影时 |
| **扩展能力** | `references/layout-dictionary.md` | 选择布局骨架（Single / Grid / Parallel 等）时 |
| | `references/style-dictionary.md` | 组合风格原子词时 |
| | `references/storyboard-mode.md` | 多帧 / 分镜 / 系列图编排时 |
| | `references/adapters.md` | 需要 VGS → 多执行视图 adapter 时 |
| | `references/brand-constraints.md` | 涉及品牌约束结构化表达时 |
| **质量 & 风险** | `references/quality-checklist.md` | Phase 3 交付前自检时 |
| | `references/vgs-validator.md` | 需要理解校验规则与风险预警时 |
| | `references/failure-modes.md` | 遇到生成失败或需要回退策略时 |
| | `references/common-pitfalls.md` | 新用户首次使用或排查常见错误时 |
| **脚本** | `scripts/validate_vgs.py` | Phase 3 校验 VGS 时 |
| | `scripts/assemble_modules.py` | 多模块深度合并时 |
| **示例** | `examples/` | 需要 single-frame / multi-block / image-to-image 示例时 |

---

## 扩展字段

以下为可选扩展字段，用于溯源、模块化组合与能力声明。不使用时 VGS 仍可正常生效。

| 能力 | 说明 |
|------|------|
| 版本标识 | 可选；建议填写如 `canonical` 用于溯源 |
| 溯源与标准化 | 可选 `metadata` 字段（spec_id / created_at / author / provenance） |
| 模块化组合 | 可选 `modules` 字段（模块继承 / overrides / 组装算法） |
| 执行层声明 | 可选 `capabilities` 字段（adapter 声明 / 参数透传） |

**何时使用扩展字段**

- **基础场景**：只需要稳定表达 Canonical VGS，本地单次生成、无需溯源、无需模块复用时，可仅使用核心字段（`task`/`canvas`/`layout`/`blocks`/`style`/`constraints`/`generation_policy`/`outputs`）
- **协作场景**：跨人协作、资产追踪、版本溯源时，添加 `metadata` 字段
- **模块化场景**：大型多块 spec 需要拆分复用时，使用 `modules` 字段
- **能力声明场景**：需要显式声明执行引擎能力（如风格迁移、局部重绘）时，使用 `capabilities` 字段

**快速入口**

- VGS Schema：`references/vgs-schema.md`（含扩展字段定义）
- 组合协议：`references/composition-protocol.md`（模块化拆分组装规则）
- 质量清单：`references/quality-checklist.md`（含四层验收标准）
- 示例：`examples/*.yaml`（包含扩展字段使用示例）
- 校验器：`scripts/validate_vgs.py`
- 模块组装器：`scripts/assemble_modules.py`（多模块深度合并 + 循环检测 + 继承解析）

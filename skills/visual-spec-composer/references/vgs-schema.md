# 视觉生成规格

VGS 是执行无关的视觉生成中间表示（IR）。它不绑定具体模型，只表达稳定的视觉意图、构图、风格、限制和执行建议。

## 设计目标

1. 对人可读，对 AI 也可解析
2. 单画面、多分块、图生图共用一套骨架
3. 支持强模型与小模型两种投影
4. 支持 references 分层与冲突消解
5. 支持 one-shot / two-stage / multi-pass 三种执行模式

---

## 2. 三层字段策略

### 最小必填层
任何 VGS 至少应包含：
- `version`
- `task`
- `input_mode.type`
- `canvas.aspect_ratio`
- `canvas.composition_mode`
- `style.genre`
- `constraints`
- `generation_policy.execution_mode`

### 增强层
复杂场景建议补充：
- `layout`
- `blocks`
- `references`
- `style.palette / lighting / detail_density`
- `constraints.text_policy`

### 专家层
高复杂度时再加：
- `reference_priority`
- `style.transition_system`
- `generation_policy.priority_order`
- `generation_policy.fallback_strategy`
- `notes`

---

## 标准模板

```yaml
version: canonical

task:
  goal: generate_image
  task_type: single_frame | multi_block | image_edit
  use_case: poster | kv | cover | concept_art | product_visual | collage | storyboard | other
  intent_summary: >
    用一句话概括这张图最终要表达什么。

input_mode:
  type: text | image | mixed
  source_images: []
  reference_images: []

canvas:
  aspect_ratio: "16:9"
  orientation: landscape | portrait | square
  size_preference: optional
  composition_mode: single_frame | multi_block | collage | split_screen | image_edit

layout:
  block_count: 1
  skeleton: centered_hero
  reading_flow: left_to_right | top_to_bottom | radial | editorial
  balance: centered | top_heavy | bottom_heavy | left_heavy | right_heavy | even | irregular
  spacing_style: seamless | separated | overlap | collage_overlap
  block_relation: single_subject | independent | same_theme_variants | same_subject_variants | sequential_narrative

blocks:
  - id: A
    role: hero | support
    subject: 主体描述
    scene: 场景描述
    emphasis: 强调点
    camera: optional
    transition_to_next: optional

style:
  genre: cinematic | commercial | editorial | illustration | anime | cyberpunk | minimal | realistic | surreal | other
  realism: photographic | semi_realistic | stylized | illustrative | 3d_cg
  palette: optional
  lighting: optional
  texture: optional
  detail_density: low | medium | high
  mood: optional
  transition_system: optional

constraints:
  must_have: []
  must_avoid: []
  text_policy:
    mode: none | reserve_area | decorative_text_like | exact_text_required
    text_area_position: optional
    text_area_priority: low | medium | high
  brand_constraints: []

references:
  - id: ref_1
    type: style | composition | subject | detail | constraint
    role: 描述该参考图在本任务中的职责
    preserve: []
    change: []
    ignore: []
    ownership:
      fields: []
    priority: 1

reference_priority:
  subject: optional
  composition: optional
  palette: optional
  lighting: optional
  texture: optional

generation_policy:
  execution_mode: one_shot | two_stage | multi_pass | brief_only
  complexity_level: low | medium | high | extreme
  small_model_mode: false
  priority_order: []
  edit_focus: []
  fallback_strategy: []

outputs:
  brief_ready: true
  canonical_vgs_ready: true
  render_views:
    - full
    - compact
    - minimal

notes:
  warnings: []
  open_questions: []
```

---

## 4. 字段解释

### 任务类型
- `goal`：当前固定为 `generate_image`
- `task_type`：任务类型，是根分支字段
- `use_case`：业务或用途层语义
- `intent_summary`：把整张图压缩成一句高信息量说明

### 输入模式
- `type`：决定后续是否需要 reference / preserve / change 逻辑
- `source_images`：原图或直接修改输入
- `reference_images`：仅作为参考的图

### 画布参数
- `aspect_ratio`：优先存逻辑比例，不强制绑定具体像素
- `composition_mode`：构图模式，比 task_type 更偏视觉结构

### 布局方式
用于多块和复杂单画面。单画面也可保留简单 skeleton。

### 分块定义
- 单画面时通常只需 1 个 block
- 多分块时 block 数应与 `layout.block_count` 一致
- `role` 区分 hero/support，便于模型抓重点

### 风格参数
不要把风格写成一串互相打架的词，尽量原子化：
- `genre`
- `realism`
- `palette`
- `lighting`
- `texture`
- `detail_density`
- `mood`

### 约束条件
把“必须有”和“绝对不要”分开写，避免自然语言混杂。

### 参考图
每张参考图都必须说明：
- 它是 style / composition / subject / detail / constraint 中的哪一种
- 保留什么
- 改什么
- 忽略什么
- 优先级如何

### 生成策略
这是连接 Canonical VGS 与执行层的桥。
- `execution_mode`：执行建议
- `complexity_level`：复杂度预算
- `small_model_mode`：是否触发降阶
- `fallback_strategy`：出现不稳定时怎么降载

---

## 小模型降阶规则

当 `small_model_mode: true` 时：

1. 优先保留：
   - 主体
   - 比例
   - 构图骨架
   - 主风格
   - 1~2 个关键限制
2. 弱化：
   - 细节修辞
   - 次要参考图
   - 复杂过渡说明
   - 多重风格混搭
3. 如 `block_count > 4`，默认警告并建议 two_stage 或 multi_pass。

---

## 6. 复杂度分级建议

### 低复杂度
- 单主体
- 单画面
- 0~1 reference
- 单风格

### 中复杂度
- 2~4 块
- 1~2 reference
- 适度过渡
- 一般一致性要求

### 高复杂度
- 5~6 块
- 多 reference
- 风格 / 构图 / 主体都要兼顾
- 强统一性要求

### 极高复杂度
- >6 块
- 精确成稿预期
- 大量禁忌项
- 多参考图且相互冲突

---

## 人类摘要模板

```md
目标：...
画布：16:9 横版，5 块拼贴，上 2 下 3
主体：...
风格：...
限制：...
执行建议：two-stage，先定布局再细化
```

---

## 8. 校验清单

生成 VGS 后至少检查：
- `layout.block_count` 与 `blocks[]` 数量是否一致
- `task.task_type` 与 `canvas.composition_mode` 是否一致
- `references` 是否缺 ownership
- `style.genre` 是否过多
- `constraints.must_have` 与 `must_avoid` 是否冲突
- `text_policy` 是否与用户预期一致

---

## 9. 扩展字段（可选）

以下三个顶层字段为可选扩展，用于支持溯源、模块化组合和能力声明。VGS 校验器会忽略未知顶层键，因此即使工具链不识别这些字段也不会报错。

### metadata — 字段溯源

记录 spec 的创建信息和字段级溯源链。

```yaml
metadata:
  spec_id: vgs-20260605-004          # 唯一标识
  created_at: '2026-06-05T14:48:20'  # ISO 8601
  author: auto-migration             # 生成者
  provenance:
    source_intent: '原始需求文本'
    derivation_chain:
      - step: canonical_vgs
        timestamp: '...'
      - step: manual_edit
        detail: '修改说明'
        timestamp: '...'
```

字段溯源规则：当多个参考图竞争同一字段时，按 `ownership.fields` 声明归属，`reference_priority` 决定冲突时的裁决优先级。

### modules — 模块化组合

将大型 spec 拆分为多个半独立模块，产出时组装为完整 spec。

```yaml
modules:
  - module_id: hero_panel
    role: hero
    extends: base_style          # 可选：继承基础风格
    override:
      blocks[0].subject: '自定义主体'
    spec:
      blocks:
        - id: hero_main
          role: hero
          subject: '主体描述'
          # ... 其余 block 字段
```

组装规则：
- `extends` 引用 `base_style` 的字段做浅层继承（override 优先）
- 组装器按 `module_id` 去重合并 blocks
- 循环检测：组装器使用三色 DFS（白→灰→黑）检测 `extends` 循环依赖
- 组装完成后剥离 `modules` 和 `capabilities`，产出纯 blocks[] 结构

### capabilities — 能力声明

声明 spec 所需的生成能力（如风格迁移、局部重绘），供 adapter 按需启用。

```yaml
capabilities:
  - name: style_transfer
    version: '1.0'
    enabled: true
    params:
      source: ref_black_gold
      targets: [palette, lighting, mood]
  - name: inpaint
    version: '1.0'
    enabled: false
    note: 声明但本任务不启用
```

能力名称使用下划线小写；`enabled: false` 表示声明但不启用，适合作为扩展点。

### 输出剥离

产出 Render Views 时，adapter 需剥离 `metadata`/`modules`/`capabilities`，只输出纯 blocks[] 结构。

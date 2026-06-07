# 适配器

VGS 是**执行无关 IR**。真正落到不同模型时，需要一层 adapter 把同一份 Canonical VGS 投影成不同执行视图。

核心原则：
- Canonical VGS 永远是源事实
- adapter 只做**投影 / 收敛 /翻译**，不应偷偷改目标
- 弱模型 adapter 可以删减，但不能改写主目标

---

## 总体架构

```text
User Intent
  ↓
Interview Tree
  ↓
Human Brief
  ↓
Canonical VGS
  ↓
Adapter Layer
  ├─ Rich Model Prompt
  ├─ Compact Prompt
  ├─ Minimal Prompt
  ├─ SD-style Positive/Negative
  ├─ Image Edit Instruction
  └─ Blockwise / Two-stage Plan
```

---

## 适配器类型

> **注**：Full/Compact/Minimal 三档基础投影规则详见 `render-views.md`。本节聚焦特殊场景 adapter。

### 稳定扩散风格适配器
适合：Stable Diffusion / ComfyUI / A1111 一类正负 prompt 结构。

建议拆成：
- `positive_prompt`
- `negative_prompt`
- `control_notes`（非 prompt 的执行注解）

映射建议：
- `must_have` → 正向 prompt
- `must_avoid` → 负向 prompt
- `references` → 不直接平铺，而是先转 ownership 语义
- `text_policy.exact_text_required` → control note，避免虚假承诺

### 图像编辑适配器
适合：图生图 / 改图 / 保主体换场景。

应明确区分三类信息：
1. **Preserve**：必须保住的内容
2. **Transform**：需要改变的内容
3. **Borrow**：只借参考图的哪些维度

输出模板建议：
- Keep: ...
- Change: ...
- Borrow only: ...
- Do not copy: ...

### 分块拼贴适配器
适合：多块拼贴、故事板、分镜、多步执行。

输出两层：
- Global layout brief
- Per-block render briefs

这样执行层可以：
- 先求布局统一
- 再逐块细化
- 最后统一色彩/光线

---

## 字段映射规则

### 任务类型映射
- `task.use_case` 决定指令语气：poster / kv / cover / product_visual / storyboard
- `task.intent_summary` 始终保留，是 adapter 的主句

### 画布参数映射
- `aspect_ratio` 必保留
- `composition_mode` 保留为结构词
- `orientation` 只有在 ratio 不够表达时才补写

### 布局与分块映射
- 强模型：可完整展开 blocks
- 小模型：只保留骨架 + 关键块数
- 极弱模型：用“centered hero / top-2-bottom-3 / split-screen”等骨架名表达

### 风格参数映射
推荐输出顺序：
1. genre
2. realism
3. palette
4. lighting
5. texture
6. mood

不要机械把所有字段平铺成一串形容词。

### 约束条件映射
- `must_have` → 正向硬要求
- `must_avoid` → 负向约束
- `text_policy` → 执行注释或单独提醒
- `brand_constraints` → 高优先级限制，不要被风格词吞没

### 参考图映射
先翻译职责，再翻译内容。

错误做法：
- 直接把多张 reference 的风格词堆进 prompt

正确做法：
- reference A controls subject
- reference B controls palette and lighting
- reference C is only a negative drift guard

---

## 小模型适配规则

当 `small_model_mode: true` 时：

1. 只保留 1 个主风格
2. 把 layout 说成人类可读骨架词
3. blocks 只保留 hero + 2~3 个关键 support
4. must_avoid 不超过 3 条
5. references 最多保留 1 主参考 + 1 辅参考
6. 优先导出 Compact，而不是 Full

---

## 5. 推荐输出格式

### 富模型提示词示例
```md
Goal: ...
Canvas: ...
Composition: ...
Subjects: ...
Style: ...
Constraints: ...
References: ...
```

### 稳定扩散风格示例
```yaml
positive_prompt: >
  ...
negative_prompt: >
  ...
control_notes:
  - ...
```

### 图像编辑示例
```yaml
keep:
  - ...
change:
  - ...
borrow_only:
  - ...
do_not_copy:
  - ...
```

---

## 设计边界

Adapter 不应该：
- 擅自新增主体
- 擅自改比例
- 擅自把 style reference 变成 subject reference
- 为了看起来更丰富而篡改 constraints

Adapter 可以：
- 压缩信息
- 重排信息
- 变换表达形态
- 针对小模型做信息收敛

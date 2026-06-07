# 规格校验器

VGS Validator 用于在真正投喂模型前，对 Canonical VGS 做**结构校验、语义一致性检查、复杂度预警、降阶建议**。

它不负责生成图片，只负责回答：

1. 这份 VGS 能不能被稳定理解？
2. 字段之间有没有自相矛盾？
3. 是否超出了 one-shot / 小模型承载能力？
4. 是否缺少关键 ownership / reference 说明？

---

## 1. 校验层级

### 结构完整性
检查必填骨架是否存在：
- `version`
- `task`
- `input_mode`
- `canvas`
- `style`
- `constraints`
- `generation_policy`

### 字段合法性
检查枚举与基础类型是否合理，例如：
- `task.task_type`
- `input_mode.type`
- `canvas.composition_mode`
- `generation_policy.execution_mode`

### 一致性检查
检查字段之间是否打架，例如：
- `layout.block_count` 与 `blocks[]` 数量不一致
- `task.task_type: multi_block` 但只有 1 个 block
- `task.task_type: image_edit` 却没有 `image`/`mixed` 输入
- `must_have` 与 `must_avoid` 出现同一约束

### 执行风险
检查是否虽然“合法”，但**大概率难生成**，例如：
- 5 块以上还要求 `one_shot`
- `small_model_mode: true` 却保留过多风格维度
- 多 reference 但未写 ownership

### 优化建议
在不改目标的前提下给出降载建议，例如：
- 把 5 块压成 3 个宏主题
- 先做 `two_stage`
- 把 style 从混合风格压成 1 个主风格

---

## 错误警告建议

### 错误级别
必须修复，否则不应进入执行层。

典型例子：
- 缺少顶层必填字段
- `blocks[]` 与 `block_count` 不一致
- reference priority 指向不存在的 reference id

### 警告级别
可以执行，但结果不稳定。

典型例子：
- 5-block + `one_shot`
- `small_model_mode` 下风格字段过多
- `image_edit` 没有显式 preserve 主体身份

### 建议级别
不是问题，只是更优做法。

典型例子：
- 先生成 Human Brief 再让用户确认
- 先出 keyframe 再做系列图
- 把风格 reference 与主体 reference 分离

---

## 3. 推荐校验规则

### 任务类型映射 / canvas 一致性
- `single_frame` 应对应 `single_frame` / `collage` 之外的单画面构图
- `multi_block` 应对应 `multi_block` / `split_screen` / `collage`
- `image_edit` 应对应 `image_edit`

### 分块规则
- 单画面允许 1 个 block
- 多块必须 `block_count >= 2`
- `blocks[].id` 不能重复
- `hero` 最好不超过 1 个；超过时至少要有主次说明

### 参考图规则
每张 reference 至少应有：
- `id`
- `type`
- `role`
- `ownership.fields`

并且：
- `style` reference 不应接管 `subject`
- `subject` reference 不应默认接管 `palette`
- 多 reference 时建议写 `reference_priority`

### 风格参数映射 规则
- `genre` 应尽量只有 1 个主风格
- `small_model_mode` 下不建议同时保留过多 style 原子字段
- `transition_system` 只在多块/拼贴时启用更合理

### 执行规则
- `block_count > 4` 且 `one_shot` → warning
- `block_count > 6` 且 `one_shot` → 强 warning
- `small_model_mode: true` + `block_count > 4` → 建议 `two_stage`
- `exact_text_required` → 默认建议后期排字

---

## 命令行用法

```bash
python3 scripts/validate_vgs.py examples/single-frame.md
python3 scripts/validate_vgs.py examples/multi-block.md --strict
python3 scripts/validate_vgs.py path/to/spec.yaml
```

说明：
- 支持直接读取 `.yaml/.yml`
- 也支持从 `.md` 中提取 ```yaml 代码块
- `--strict` 下 warning 也会使退出码非 0

---

## 5. 推荐接入点

在 visual-spec-composer 工作流中，推荐顺序：

1. 访谈完成
2. 产出 Human Brief
3. 产出 Canonical VGS
4. **先跑 Validator**
5. 再导出 Render Views / adapter outputs

---

## 不做的事

Validator 不负责：
- 判断审美是否高级
- 判断模型一定能画出来
- 自动替你重写成完美 prompt

它只负责把“明显结构风险”拦在执行层前。

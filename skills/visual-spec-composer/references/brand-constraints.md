# 品牌约束

`constraints.brand_constraints` 用于表达**品牌级硬约束**，避免在 VGS 中只靠零散自然语言去描述品牌要求。

它适合：
- 品牌色锁定
- 禁色
- logo 使用规则
- 文本留白区
- 字体 / 版式气质要求
- 产品外观不可改动项
- 合规或法务限制

---

## 1. 推荐数据形态

推荐 `brand_constraints` 为对象数组，而不是纯字符串数组：

```yaml
constraints:
  brand_constraints:
    - id: brand_palette
      type: palette_lock
      mode: hard
      priority: 1
      apply_to:
        - global
      value:
        primary:
          - "#0F62FE"
        secondary:
          - "#DDEBFF"
        tolerance: low
    - id: no_competitor_red
      type: palette_ban
      mode: hard
      priority: 2
      apply_to:
        - global
      value:
        banned_colors:
          - "#FF0000"
```

---

## 常见约束类型

### 色板锁定
锁定主色 / 辅色 / 容差。

字段建议：
- `primary`
- `secondary`
- `accent`
- `tolerance`：low / medium / high

### 色板禁用
禁用某些颜色或色系。

适合：
- 竞品主色规避
- 法务禁色
- 品牌低端感规避

### 标识策略
控制 logo 是否出现、出现在哪、大小大概如何。

字段建议：
- `presence`: required / optional / forbidden
- `position`
- `safe_margin`
- `dominance`: low / medium / high

### 字体区域
不是让模型精准排版，而是定义**留字区域**。

字段建议：
- `position`
- `size_ratio`
- `background_cleanliness`
- `avoid_overlap_with_subject`

### 字体风格
表达字体气质，而不是精确字体文件。

字段建议：
- `tone`: premium_modern / tech_clean / editorial / playful / luxury
- `weight_bias`
- `case_preference`

### 产品标识锁定
锁定产品外形特征。

字段建议：
- `must_preserve`
- `must_not_change`
- `tolerance`

### 合规规则
法务 / 行业限制。

例如：
- 不出现医疗承诺式视觉暗示
- 不出现未授权 UI 样式
- 不出现儿童误导性场景

---

## 3. 通用字段建议

每条 brand constraint 建议具备：
- `id`
- `type`
- `mode`: hard / soft
- `priority`
- `apply_to`: global / block ids
- `value`
- `notes`（可选）

其中：
- `hard`：adapter 不应随意删掉
- `soft`：在小模型降阶时可被压缩

---

## 文本策略关系

- `text_policy` 解决“是否要文字、文字是否必须精确”
- `brand_constraints` 解决“品牌留字区、品牌视觉纪律、logo 规则”

两者互补，不要混写。

---

## 参考图关系

品牌约束不等于 reference。

- reference 解决“借谁的风格/构图/主体”
- brand constraint 解决“即使参考图这么做，我也不能越界到哪”

例如：
- 可以参考某广告图的黑金气质
- 但品牌约束可能禁止使用过暗背景或禁止红色光源

---

## 适配器应用规则

Adapter 在投影时应：

1. 先处理 `hard` 品牌约束
2. 再处理主体与布局
3. 再处理风格润色

换句话说：
- 品牌约束优先级通常高于 mood 修辞
- 不应让“更酷的风格词”覆盖“品牌硬限制”

---

## 7. 小模型降阶建议

小模型下，不要把品牌约束写得像法务长文。

建议压成三层：
1. 保住主色 / 禁色
2. 保住留白区 / logo presence
3. 其余作为 notes，不进 Compact Prompt

---

## 示例

```yaml
constraints:
  must_have:
    - premium product focus
  must_avoid:
    - fake text
  text_policy:
    mode: placeholder_allowed
    text_area_position: left
    text_area_priority: high
  brand_constraints:
    - id: left_copy_zone
      type: typography_zone
      mode: hard
      priority: 1
      apply_to: [global]
      value:
        position: left
        size_ratio: 0.28
        background_cleanliness: high
        avoid_overlap_with_subject: true
    - id: blue_palette
      type: palette_lock
      mode: hard
      priority: 2
      apply_to: [global]
      value:
        primary: ["#0A84FF"]
        secondary: ["#D9ECFF"]
        tolerance: medium
```

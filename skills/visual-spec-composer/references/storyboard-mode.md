# 故事板模式

当用户要的不是一张图，而是一组**连续画面 / 分镜 / 关键帧 / 系列封面**时，不应把所有信息硬塞进一个 VGS。

推荐做法：
- **单帧继续用 Canonical VGS**
- **多帧用 Sequence Wrapper 包一组 VGS**

这样不会污染单图 schema，又能覆盖故事板场景。

---

## 设计理由

因为多帧任务比单帧多出以下问题：
- 帧间连续性
- 角色一致性
- 场景推进
- 镜头语言变化
- 重复元素的稳定继承
- 哪些必须不变，哪些应该变化

这些问题属于**序列层**，不属于单帧层。

---

## 序列包装格式

```yaml
version: canonical
sequence:
  sequence_id: demo_story_01
  use_case: storyboard | campaign_series | keyframes | scene_sequence
  global_goal: >
    用一句话描述整个序列在讲什么。
  global_style:
    genre: cinematic
    realism: semi_realistic
    palette: cool_blue
    lighting: volumetric
    mood: epic
  continuity_rules:
    must_repeat:
      - protagonist identity
      - costume silhouette
      - core palette
    may_change:
      - camera distance
      - pose
      - scene detail
    must_avoid:
      - face drift
      - era drift
  execution_policy:
    mode: keyframe_first | shot_by_shot | cluster_pass
    small_model_mode: false
frames:
  - frame_id: F01
    beat: establish world
    vgs_ref: inline_or_external
  - frame_id: F02
    beat: introduce action
    vgs_ref: inline_or_external
```

---

## 3. 帧层建议字段

每一帧建议补这些序列字段：

- `frame_id`
- `beat`：这帧在叙事中承担什么功能
- `continuity_anchor`：和前一帧必须继承什么
- `delta_from_previous`：与前一帧刻意变化什么
- `importance`：hero / support / bridge
- `transition_hint`：切换方式

示例：

```yaml
- frame_id: F03
  beat: reveal the device core
  continuity_anchor:
    - same product identity
    - same black-gold palette
  delta_from_previous:
    - tighter camera
    - stronger rim light
  importance: hero
  transition_hint: push-in reveal
```

---

## 连续性拆解方法

把连续性拆成 5 类，不要混着写：

1. **identity continuity**
   - 人物脸
   - 产品外形
   - 服装轮廓
2. **style continuity**
   - palette
   - lighting logic
   - texture language
3. **world continuity**
   - 时代感
   - 空间设定
   - 道具系统
4. **camera continuity**
   - 镜头组的推进逻辑
5. **narrative continuity**
   - 每帧承担的叙事功能

---

## 5. 推荐执行模式

### 关键帧优先
先定义 3~5 个关键帧，再扩展中间帧。

适合：
- 故事板
- 广告分镜
- 小模型环境

### 逐帧推进
每一帧都独立精修，再靠 continuity rules 维持统一。

适合：
- 重点帧都很重要
- 每帧差异较大

### 分组处理
先按场景或阶段分组，再分别生成。

适合：
- 长序列
- campaign series
- 海报系列

---

## 小模型支持策略

如果 `small_model_mode: true`：

1. 不要一口气让模型理解整个故事板
2. 先做 keyframe
3. 每次只喂 1 帧 + 2~4 条 continuity anchors
4. 连续性优先级：
   - identity
   - palette
   - silhouette
   - camera progression
5. 把全局 style 压成 1 主风格 + 1 主 palette

---

## 7. 典型场景

### 场景广告三连图
- Frame 1：产品建立镜头
- Frame 2：功能特写
- Frame 3：品牌收束英雄镜头

### 场景概念分镜
- F01 世界建立
- F02 主体出现
- F03 冲突升级
- F04 动作高潮
- F05 结果呈现
- F06 收束镜头

### 场景角色海报系列
- 保持角色 identity、服装轮廓与主 palette
- 变化场景、角度、情绪

### 场景产品广告完整示例

目标：同一款黑金悬浮设备，做 3 帧广告分镜；保持产品身份与主色稳定，但镜头逐步推进。

```yaml
version: canonical
sequence:
  sequence_id: product_ad_triptych_01
  use_case: storyboard
  global_goal: >
    用 3 帧完成“建立产品 → 展示功能 → 英雄收束”的广告分镜。
  global_style:
    genre: premium_tech
    realism: semi_realistic
    palette: black_gold
    lighting: rim_light + volumetric haze
    mood: futuristic_luxury
  continuity_rules:
    must_repeat:
      - same product identity
      - same black-gold palette
      - same floating device silhouette
    may_change:
      - camera distance
      - environment detail
      - motion intensity
    must_avoid:
      - product shape drift
      - material drift
      - era drift
  execution_policy:
    mode: keyframe_first
    small_model_mode: true
frames:
  - frame_id: F01
    beat: establish product
    continuity_anchor:
      - same device silhouette
      - black-gold palette
    delta_from_previous:
      - none (opening frame)
    importance: hero
    transition_hint: clean establish shot
    vgs:
      task:
        task_type: single_frame
        use_case: product_key_visual
      canvas:
        aspect_ratio: 16:9
        orientation: landscape
      subject:
        primary: black-gold floating device
      composition:
        shot_type: wide
        focus: centered hero object
      style:
        genre: premium_tech
        lighting: rim light
        mood: futuristic_luxury
  - frame_id: F02
    beat: reveal function detail
    continuity_anchor:
      - same product identity
      - same material finish
    delta_from_previous:
      - tighter camera
      - stronger glow on functional area
    importance: support
    transition_hint: push-in
    vgs:
      task:
        task_type: single_frame
        use_case: feature_closeup
      canvas:
        aspect_ratio: 16:9
        orientation: landscape
      subject:
        primary: same device close-up
      composition:
        shot_type: medium_close
        focus: feature highlight
      style:
        genre: premium_tech
        lighting: dramatic accent light
        mood: precise_high_end
  - frame_id: F03
    beat: brand hero close
    continuity_anchor:
      - same product identity
      - same black-gold palette
    delta_from_previous:
      - cleaner background
      - stronger symmetry
    importance: hero
    transition_hint: resolve to packshot-like hero shot
    vgs:
      task:
        task_type: single_frame
        use_case: closing_hero_frame
      canvas:
        aspect_ratio: 16:9
        orientation: landscape
      subject:
        primary: same device hero shot
      composition:
        shot_type: medium
        focus: centered hero + tagline area
      style:
        genre: premium_tech
        lighting: polished studio glow
        mood: brand_confident
```

为什么这个示例重要：
- 演示了 **Sequence Wrapper + frame-level VGS** 的嵌套关系
- 演示了 `must_repeat / may_change / must_avoid` 的实际写法
- 演示了 small model 下如何用 `keyframe_first` 保持稳定

---

## 与单帧规格的边界

单帧 VGS 只回答：
- 这一张图怎么长

Sequence Wrapper 回答：
- 这一组图彼此如何保持一致并逐步推进

所以 storyboard mode 是**单帧 VGS 之上的编排层**，不是替代层。

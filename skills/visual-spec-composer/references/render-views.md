# 渲染视图

本文件定义如何把 Canonical VGS 投影成不同模型可读视图。

## 三种渲染视图

### 完整提示词
适合：强模型、长上下文模型、需要更高控制度的模型

保留：
- 任务目标
- 画布比例
- 构图骨架
- 主体与场景
- 风格全量字段
- 核心限制
- references 摘要

### 紧凑提示词
适合：普通模型、小模型、易跑偏模型

只保留：
- 用途
- 比例
- 主体
- 构图骨架
- 主风格
- 1~2 个限制
- 必要时的块数说明

### 最小提示词
适合：极弱模型、首次试投、快速试探

只保留：
- 主体
- 比例
- 一个构图关键词
- 一个风格关键词
- 一个限制

---

## 完整提示词生成规则

推荐顺序：
1. 用途 / 目标
2. 画布比例与构图模式
3. 主体与场景
4. 多块结构（如有）
5. 风格系统
6. references 摘要
7. 关键限制与避免项
8. 执行提示（如保留留白、避免乱码字）

### 完整提示词 模板
```md
Create a [use_case] image in [aspect_ratio] with a [composition_mode / skeleton] layout.
Main subject: ...
Scene/background: ...
If multi-block: block structure is ...; block A shows ...; block B shows ...
Style: [genre], [realism], [palette], [lighting], [texture], [mood].
Preserve / borrow from references: ...
Constraints: must have ...; avoid ...
```

---

## 紧凑提示词生成规则

压缩时优先保留：
- 主体
- 画幅
- 主骨架
- 主风格
- 关键限制

删减顺序：
1. 次要块细节
2. 次要 references
3. mood 修辞
4. 次级材质描述
5. 复杂过渡说明

### 紧凑提示词 模板
```md
[aspect_ratio] [use_case], [main subject], [layout skeleton], [main style], [scene/background], reserve [text area if needed], avoid [top 1~2 failures].
```

---

## 最小提示词生成规则

模板：
```md
[main subject], [aspect_ratio], [core composition], [core style], avoid clutter.
```

只适合：
- 做快速方向验证
- 探测模型是否理解主意图
- 给极短上下文模型做第一轮尝试

---

## 多块图特殊规则

如果 `layout.block_count >= 5`：
- Full Prompt 仍可描述各块
- Compact Prompt 只保留：
  - 块数
  - 骨架
  - 主块 / 辅块关系
  - 整体统一风格
- Minimal Prompt 不展开逐块内容

若模型较弱：
- 明确建议 `two_stage` 或 `multi_pass`
- 不要把每块细节全塞进 Compact Prompt

---

## 参考图投影规则

### 风格参考
转成：
- keep palette / lighting / mood from reference

### 构图参考
转成：
- follow the layout logic / spatial balance / negative space approach

### 主体参考
转成：
- preserve subject identity / product appearance / key silhouette

### 细节参考
转成：
- borrow material / surface / costume / local design language

### 约束参考
转成：
- stay away from ... / avoid drifting toward ...

---

## 输出视图质量要求

### 完整视图
- 不遗漏主要块
- 不把 reference 角色写混
- 不出现明显字段冲突

### 紧凑视图
- 读起来像一句高信息量指令，而不是清单堆砌
- 不超过模型承载阈值

### 最小视图
- 仍能保住主体、比例、风格主方向

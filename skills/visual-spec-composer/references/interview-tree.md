# 访谈问题树

本文件定义访谈树、提问顺序、分支规则，以及“问题 → VGS 字段”的映射。

## 访谈总原则

1. 一次只问一个问题。
2. 每个问题只解决一个决策。
3. 每个问题附推荐答案或候选。
4. 能从上下文推断的，不重复问。
5. 简单任务控制在 4~6 轮；复杂任务再展开子树。
6. 用户明确只要快速版时，优先生成 quick brief，再补字段。
7. 用户若说“重来 / 回到上一步 / 只改某一项”，只回滚受影响字段，不整棵树重问。

---

## 2. 根路由问题

### 任务类型确认
候选：
- 单画面生成
- 多分区 / 拼贴图
- 基于已有图片改造
- 连续画面 / 分镜 / 系列图
- 不确定，请帮我判断

映射：
- `task.task_type`
- `canvas.composition_mode`
- `input_mode.type`

路由说明：
- 若为“连续画面 / 分镜 / 系列图”，转入 `references/storyboard-mode.md`
- storyboard 是序列编排层；每一帧仍复用本访谈树中的单帧 / 多块问题

### 模糊需求澄清

不要直接生成 prompt。改为推荐三个方向让用户选：

> 你只描述了一种感觉，我来帮你拆成三个可选方向，你选一个或告诉我哪个最近：
> - **A. 科幻冷峻**：黑蓝色调、霓虹光带、机械质感、未来城市
> - **B. 极简高奢**：大留白、金属银、无衬线字体、单一主体
> - **C. 数字艺术**：粒子流、光轨、3D 渐变、抽象空间感

用户选定后继续正常流程（→ Q1）。

映射：
- `task.intent_summary`
- `style.genre`

---

### 使用场景确认
候选：
- 海报 / KV
- 封面
- 社媒配图
- 产品主视觉
- 概念图
- 拼贴图
- 分镜帧
- 其他

映射：
- `task.use_case`
- `task.intent_summary`

### 起点确认
候选：
- 纯文本描述
- 有原图要改
- 有参考图但不是原图
- 文字 + 图片混合

映射：
- `input_mode.type`
- `input_mode.source_images`
- `input_mode.reference_images`

### 画布比例确认
候选：
- 16:9 横版
- 9:16 竖版
- 1:1 方图
- 4:3
- 自定义

映射：
- `canvas.aspect_ratio`
- `canvas.orientation`

---

## 3. 单画面子树

### 主体内容
候选：
- 人物
- 产品
- 建筑 / 空间
- 场景
- 抽象视觉
- 多主体同一空间

映射：
- `blocks[0].subject`
- `task.intent_summary`

### 背景场景
候选：
- 纯背景
- 室内
- 城市
- 自然
- 科幻空间
- 抽象空间
- 不确定，请推荐

映射：
- `blocks[0].scene`

### 构图方式
候选：
- 居中主体
- 左文右图
- 右文左图
- 三分法
- 特写
- 远景
- 留白型
- 对角线动势

映射：
- `layout.skeleton`
- `blocks[0].camera`
- `constraints.text_policy`

### 风格定位
推荐拆问成 1 个主问题 + 必要追问：
- 主风格：电影感 / 商业广告 / 插画 / CG / 极简 / 赛博朋克 / 杂志感
- 真实度：摄影 / 半写实 / 插画 / 3D
- 色调：冷 / 暖 / 黑金 / 高饱和 / 低饱和
- 光线：柔光 / 硬光 / 逆光 / 霓虹 / 体积光

映射：
- `style.genre`
- `style.realism`
- `style.palette`
- `style.lighting`

### 约束条件
候选：
- 需要留标题区
- 需要品牌色
- 不要假文字
- 不要过于杂乱
- 不要卡通化

映射：
- `constraints.must_have`
- `constraints.must_avoid`
- `constraints.text_policy`

---

## 多分区拼贴子树

### 分块数量
候选：2 / 3 / 4 / 5 / 6 / 自定义

映射：
- `layout.block_count`

### 版式结构
候选：
- 上2下3
- 左大右小
- 右大左小
- 中心主图 + 四周辅助
- 2x2 网格
- 杂志拼贴
- 条带叙事
- 不确定，请推荐

映射：
- `layout.skeleton`
- `layout.reading_flow`

### 块间关系
候选：
- 独立内容
- 同主题不同切面
- 同主体不同视角
- 连续叙事
- 风格拼贴

映射：
- `layout.block_relation`
- `generation_policy.priority_order`

### 分块内容定义
对每个 block 询问：
1. 这块展示什么主体？
2. 这块场景是什么？
3. 是主块还是辅助块？
4. 强调什么细节？
5. 如何和下一块衔接？

映射：
- `blocks[].id`
- `blocks[].role`
- `blocks[].subject`
- `blocks[].scene`
- `blocks[].emphasis`
- `blocks[].transition_to_next`

### 过渡风格
候选：
- 硬分割
- 色彩渐变
- 光线延续
- 烟雾 / 流体连接
- 粒子 / 线条贯穿
- 拼贴覆盖边缘

映射：
- `layout.spacing_style`
- `style.transition_system`

### 整体节奏
候选：
- 上重下轻
- 上轻下重
- 中心最强
- 左右对冲
- 均衡网格
- 不规则杂志感

映射：
- `layout.balance`
- `style.detail_density`

---

## 5. 图生图 / 改图子树

### 角色定位
候选：
- 原图改造
- 只做风格参考
- 只做构图参考
- 主体参考
- 多图混合参考

映射：
- `references[].type`
- `references[].role`

### 保留内容
候选：
- 主体
- 构图
- 姿态
- 色调
- 光线
- 材质
- 只保留氛围

映射：
- `references[].preserve`
- `constraints.must_have`

### 修改内容
候选：
- 风格
- 背景
- 光线
- 配色
- 服装 / 材质
- 场景氛围
- 画幅裁切

映射：
- `references[].change`
- `generation_policy.edit_focus`

### 新增元素
候选：
- 不加
- 少量装饰
- 新辅助主体
- 新文字区
- 改成拼贴结构

映射：
- `constraints.must_have`
- `layout.block_count`
- `canvas.composition_mode`

---

## 参考图补充

### 参考图职责
候选：
- 风格
- 构图
- 主体
- 细节
- 约束

映射：
- `references[].type`
- `references[].ownership`

### 优先级排序
映射：
- `references.priority`
- `references.ownership`

### 排除内容
映射：
- `references[].ignore`
- `constraints.must_avoid`

---

## 7. 小模型 / 执行策略问题

### 目标模型
候选：
- 强模型
- 普通模型
- 小模型 / 短上下文模型
- 不确定，先都给

映射：
- `generation_policy.small_model_mode`
- `outputs.model_views`

### 执行方式
候选：
- 一次直接生成
- 先出粗构图再细化
- 分块生成再统一
- 先出规格，不急着执行

映射：
- `generation_policy.execution_mode`

---

## 回退与收尾

### 回退规则
- “重来” → 先确认是全量重来，还是只重来主体 / 构图 / 风格 / references / 执行策略
- “回到上一步” → 只撤销上一问题对应字段，再继续下一问
- “只改 X” → 仅修改受影响字段，其余已确认内容保持不变

### 结束前检查问题

如果以下任一项未确定，应优先补问：
- 主要用途
- 画布比例
- 主体
- 风格主方向
- 是否分块
- 是否有关键参考图
- 是否留文字区

---

## 9. 简化版字段映射表

| 问题 | VGS 字段 |
|---|---|
| 任务类型 | `task.task_type`, `canvas.composition_mode` |
| 用途 | `task.use_case`, `task.intent_summary` |
| 输入方式 | `input_mode.type`, `input_mode.*` |
| 比例 | `canvas.aspect_ratio`, `canvas.orientation` |
| 分块数 | `layout.block_count` |
| 版式骨架 | `layout.skeleton`, `layout.reading_flow` |
| 每块内容 | `blocks[]` |
| 风格 | `style.*` |
| 参考图职责 | `references[]` |
| 保留/修改 | `references[].preserve`, `references[].change` |
| 限制项 | `constraints.*` |
| 小模型模式 | `generation_policy.small_model_mode` |
| 执行方式 | `generation_policy.execution_mode` |

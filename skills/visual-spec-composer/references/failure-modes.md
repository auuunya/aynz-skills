# 失效模式与回退策略

## 常见失败点

1. **需求过散**：用户没有主目标，提了很多"感觉"和"可能"，难以锁定 task_type
2. **Reference 冲突**：多张参考图互相矛盾，且未定义 ownership，导致风格混乱
3. **分块堆砌**：块数过多、风格词堆砌，块与块之间互相抵消，整体失去焦点
4. **目标错位**：用户要精确排版成稿，但走的是生图路径；期望 ≠ 生图能力上限
5. **只有感觉词**：用户只说“未来感 / 高级感 / 酷”，没有主体、用途、画幅等可执行信息
6. **连续性失控**：多帧/系列图只写了每帧内容，没写 continuity rules，导致角色脸、时代感、主色漂移
7. **参考图职责混乱**：把 source image、style reference、layout reference 混成一类，既想保留外形又想完全改写
8. **小模型过载**：任务本身可做，但一次喂入的信息量超过小模型稳定承载上限

---

## 回退策略

| 失败点 | 回退动作 |
|---|---|
| 需求过散 | 先锁定"这张图是干什么的"，其余全部默认；产出 brief_only，不强行出 VGS |
| Reference 冲突 | 压成 1 主参考 + 其余降为文字约束；显式写入 conflict note |
| 分块过多 | 降为单画面或 2~4 块；超 4 块推 two_stage，超 6 块禁止 one_shot |
| 目标错位 | 明确告知执行限制；产出 VGS + Minimal Prompt 先试投，不承诺精确成稿 |
| 只有感觉词 | 不直接生成；先给 3 个方向候选（如科幻冷峻 / 极简高奢 / 数字艺术），让用户选方向再继续 |
| 连续性失控 | 从单帧 VGS 升格为 Sequence Wrapper；至少补 `must_repeat / may_change / must_avoid` 三类规则 |
| 参考图职责混乱 | 把图片按 `source / style / composition / detail` 四类重标；保留项与可改项分开写 |
| 小模型过载 | 切 small_model_mode；先出 Human Brief，再压成 Compact Prompt，必要时拆成 keyframe-first |

---

## 降阶决策树

```
复杂度评估
├── block_count > 6 → 禁止 one_shot，推 two_stage / multi_pass
├── block_count > 4 → 警告，建议 two_stage
├── reference 冲突 → 指定 ownership，或合并为文字描述
├── multi_frame 且无 continuity rules → 先补 Sequence Wrapper，再生成单帧 VGS
├── 只有感觉词 → 先做方向澄清，不直接出 prompt
├── small_model_mode → 强制 Compact Prompt，收敛风格词 ≤1 主词
└── 需求模糊 → brief_only，不出 VGS，先问清目标
```

---

## 诚实边界

以下场景应在 Brief 中**主动说明执行限制**，不应伪装成稳态任务：

- 精确文字排版（需要后期合成）
- 多图精确位置对齐（设计软件能力域）
- 高精度品牌规范终稿
- 超过 6 块且要求相互精确衔接的拼贴图
- 超长连续分镜且要求角色/场景/道具全程零漂移
- 同时要求“完全保留原图结构”与“完全换成另一张参考图风格+构图”

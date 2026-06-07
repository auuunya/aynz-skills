# 风格词典

本词典用于把“风格”拆成几个更稳定的原子字段，减少 prompt 里互相打架的形容词堆砌。

## 风格原子字段

### 风格流派
大的视觉流派。
候选示例：
- cinematic
- commercial
- editorial
- realistic
- minimal
- cyberpunk
- futuristic
- anime
- illustration
- fantasy
- surreal
- luxury

### 写实度
真实度层。
候选示例：
- photographic
- semi_realistic
- stylized
- illustrative
- 3d_cg

### 色板
色彩系统。
候选示例：
- cool_blue
- warm_gold
- black_gold
- monochrome
- pastel
- high_saturation
- low_saturation
- neon_mix
- earth_tone

### 光照
光线系统。
候选示例：
- soft_light
- hard_light
- rim_light
- backlight
- volumetric_light
- neon_light
- studio_lighting
- ambient_diffuse

### 质感
材质 / 表面语言。
候选示例：
- glossy
- matte
- metallic
- glassy
- paper_cut
- grainy
- painterly
- clean_polished

### 细节密度
信息密度。
候选示例：
- low
- medium
- high

### 氛围
气质层。
候选示例：
- epic
- calm
- elegant
- mysterious
- playful
- tense
- premium
- dreamy
- dramatic

---

## 2. 推荐写法

优先按以下顺序填写：
1. `genre`
2. `realism`
3. `palette`
4. `lighting`
5. `texture`
6. `detail_density`
7. `mood`

示例：
```yaml
style:
  genre: cinematic
  realism: semi_realistic
  palette: cool_blue
  lighting: volumetric_light
  texture: metallic
  detail_density: medium
  mood: epic
```

---

## 冲突警报

以下组合应谨慎：
- minimal + ultra high detail everywhere
- monochrome + high saturation neon mix
- soft_light + extreme hard shadow everywhere
- clean_polished + heavy dirty grainy texture

如果用户真想混合，应该明确：
- 谁是主风格
- 谁只作用于局部
- 谁只是 mood，不进入硬约束

---

## 4. 小模型收敛规则

小模型下建议：
- `genre` 最多 1 个主风格
- `mood` 最多 1 个
- `palette` 只保留 1 套
- `lighting` 只保留 1 套
- `detail_density` 不要同时要求“极简 + 海量元素”

---

## 风格转文字建议

把 style 转成 render prompt 时：
- 先输出主风格与真实度
- 再补色彩与光线
- 最后补材质与 mood
- 不要把所有词机械平铺

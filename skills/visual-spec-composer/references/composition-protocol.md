# 组合协议

## 概述

VGS 的 `modules` 允许将一个大型 spec 拆分为多个半独立模块，在产出时组装为完整 spec。

## 设计目标

1. 大型多块 spec 可按块拆分，降低单次编辑复杂度。
2. 模块可继承共享配置（如统一风格），减少重复。
3. 模块可独立修改局部字段而不影响整体。
4. 组装后产出的完整 spec 必须与单体 spec 等价。

## 模块结构

```yaml
modules:
  - module_id: hero_panel      # 唯一小写蛇形标识
    role: hero                  # hero / support / accent / caption
    extends: base_style         # 可选：继承基础风格
    override:                   # 可选：点路径覆盖
      blocks[0].subject: '自定义主体'
    spec:                       # 模块独立 spec
      blocks:
        - id: hero_main
          role: hero
          subject: '...'
```

## 继承规则

- `extends` 引用的 `base_style` 定义在 spec 顶层（非 modules 内）
- 继承为浅层合并：模块 spec 优先，base_style 补缺
- `override` 优先于模块 spec

## 循环检测

组装器使用三色 DFS 检测 `extends` 循环依赖：
- 白色：未访问
- 灰色：正在访问（在栈中）
- 黑色：已完成

若在 DFS 中遇到灰色节点，判定为循环并报错。

## 组装流程

1. 验证无循环依赖
2. 对每个模块执行继承解析（extends → override → spec）
3. 按 module_id 合并 blocks（浅层去重追加）
4. 剥离 `modules` 和 `capabilities`
5. 产出纯 blocks[] 结构的完整 spec

## 冲突消解

当多个模块的参考图竞争同一字段时，按 `ownership.fields` 声明归属，`reference_priority` 决定裁决优先级。

## 注意事项

- `modules` 是编辑时结构，产出 Render Views 时会被剥离
- Adapter 操作的是 `blocks[]`，不是 `modules[]`

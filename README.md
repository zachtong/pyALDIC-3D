# pyALDIC-3D

**Stereo-DIC (3D digital image correlation) desktop application, built on the pyALDIC-2D platform.**

> 状态 / Status: **pre-development（仅文档）**。本仓库当前只包含架构基线与开发路线文档；
> 代码从 Phase 0 开始进入（见 `docs/architecture/03_opus_phase_prompts.md`）。

## 这是什么

pyALDIC-3D 是一个**独立应用程序**：拥有自己的工程架构（project schema、状态管理、
工作流控制器、3D 可视化层），构建在成熟的 pyALDIC-2D 平台之上（复用其 DIC 引擎、
I/O、网格处理、GUI 组件与导出基础设施，以库依赖方式引入，不修改 2D 主线）。

核心算法（立体匹配、时序追踪、三角化重建、标定导入、3D 表面应变）以 MATLAB 版
`3D-Stereo-ALDIC`（Exp. Mech. 2025, DOI 10.1007/s11340-025-01225-7）为数学参考，
但**不做机械翻译**——移植的是数学与流程，不是 MATLAB 的簿记方式。

## 相关代码库（兄弟目录）

> 均为本仓库的**兄弟目录**（同一 `MATLABCodes/` 父目录下）。相对路径跨机器稳健；
> 绝对路径前缀可能因机器而异，以兄弟关系为准。开发会话请把工作目录设在本文件夹，
> 使下列 `../` 路径可直接解析。缺失时可从 GitHub clone 到对应兄弟位置。

| 仓库（相对路径） | 角色 | GitHub |
|---|---|---|
| `../pyALDIC` | 2D 平台（包 `al-dic`，PyPI 已发布 v0.7.0）——库依赖，只经声明缝隙修改 | `zachtong/pyALDIC` |
| `../3D-Stereo-ALDIC` | MATLAB 算法参考（只读；只信任 `gui/runPipelineCore.m` 主路径） | `zachtong/3D-Stereo-ALDIC` |
| `../StereoDIC_Challenge_1`, `../StereoDIC_Challenge_2` | 验证数据集 | — |
| `../ADIC3D-main`, `../MultiDIC-1.1.0` | 第三方立体 DIC 实现（策略对照参考） | — |

## 文档导航

从 **`docs/architecture/00_INDEX.md`** 开始，它包含阅读顺序、决策日志与阶段交接协议。

| 文档 | 内容 |
|---|---|
| `docs/architecture/00_INDEX.md` | 索引、决策日志（D1–D11，已全部拍板）、交接协议 |
| `docs/architecture/01_technical_baseline.md` | 技术基线 v1.1：总体判断、软件架构、复用清单、MATLAB 使用方式（含 acc/inc 语义理清）、数据结构、GUI workflow、分期路线 |
| `docs/architecture/02_correspondence_strategies.md` | 立体/时序对应策略调研（4 种策略利弊、误差传播、可插拔接口设计） |
| `docs/architecture/03_opus_phase_prompts.md` | 交给代码模型（Opus 等）的分阶段执行指令 |

## 如何开始开发（Phase 0）

本仓根目录的 **`CLAUDE.md` 会被 Claude Code 自动加载**（含 Master Preamble：身份、
仓库位置、架构不变量、工程规则），所以开发会话**只需粘贴 Phase Prompt**，无需再贴 Preamble。

1. 阅读 `docs/architecture/00_INDEX.md`（决策日志 + 交接协议）与 `01_technical_baseline.md`；
2. **Phase 0**：在**本仓**工作区的会话里，粘贴 `03` 的 *Phase 0* prompt——建脚手架、`git init`（不碰 2D）；
3. 之后 Phase 1–5 各自一个会话，均在本仓工作区，粘贴对应 Phase Prompt；
4. 每阶段结束于"门禁"（测试 + 对位指标 + PDF 报告），经用户确认后才进入下一阶段。

> 权限：两个参考仓（`../pyALDIC`、`../3D-Stereo-ALDIC`）**全程只读**——`.claude/settings.json`
> 已放行读、deny 写。所有阶段都在本仓工作、不改 2D（决策 D11）。

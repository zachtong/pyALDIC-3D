# pyALDIC-3D 技术基线（Technical Baseline）v1.1

> 产出：2026-07-02，基于对 pyALDIC-2D（`../pyALDIC`，33,356 行 Python）与 MATLAB
> `3D-Stereo-ALDIC`（273 个 .m 文件）的代码级核查。所有关键论断均附 file:line 证据
> （见附录）。v1.1 相对会话内 v1.0 的修订见 `00_INDEX.md` Changelog。
> 立体/时序对应策略的深入分析在 `02_correspondence_strategies.md`；分阶段执行指令在
> `03_opus_phase_prompts.md`。

---

## A. 总体技术判断

**pyALDIC-3D 是一个独立应用程序，构建在 pyALDIC-2D 平台之上；MATLAB 3D-ALDIC 仅作为
数学参考和验收基准。**

定位的两个面，缺一不可：

- **独立应用**：pyALDIC-3D 拥有自己的仓库、包（import 名 `al_dic_3d`，PyPI 发布名 `al-dic-3d`，决策 D8）、project schema
  （`.aldic3d` 会话格式）、应用状态管理（`AppState3D`）、工作流控制器与 3D 可视化层。
  它不是 2D 软件内部的一个"3D 模式"，可独立安装、独立发版、独立演进。
- **平台复用**：2D 的 DIC 引擎、I/O、网格处理、通用 GUI 组件、导出基础设施以
  **只读锁定库**方式引入（`al-dic==0.6.*`，开发期 editable install `../pyALDIC`），
  **默认不改 2D 一行**（决策 D11）；需要的 2D 内部直接 import 并在 `docs/DEPENDS_ON_2D.md`
  记账。2D 主线零改动、零风险。

这个判断由三条已验证的事实支撑：

1. **2D 引擎就是 3D 的计算主力，接缝已存在。** 立体 DIC 的全部相关运算都发生在 2D
   图像对之间（跨相机匹配 + 每相机时序追踪），第三维由标定几何三角化得出，不参与
   相关求解。`run_aldic()` 已接受外部 `mesh`/`U0`/`compute_strain=False`
   （`core/pipeline.py:551-560`），`need_fft = dic_mesh is None or current_U0 is None`
   （`:887`）允许从任意种子出发做纯 IC-GN+ADMM。跨相机匹配需要的调用模式一行引擎
   代码都不用改。
2. **MATLAB 版最混乱、最易错的 acc/inc 簿记，pyALDIC-2D 已用更好的抽象解决。**
   `FrameSchedule`（任意帧配对调度，acc/inc 只是两个特例，`core/data_structures.py:52`）
   + `_compute_cumulative_displacements_tree`（树状"增量→累积"变换，`core/pipeline.py:417`，
   已含"在变形后位置插值增量"的正确实现）是已发布、已测试的代码。从 MATLAB 重构
   等于把已修好的 bug 再修一遍。
3. **MATLAB 代码库只具备"被参考"资格，不具备"被移植"资格。** `TemporalMatch` 有
   7 个变体共 3,745 行而正式流水线只调用 1 个；4 套平行位移表示；`try/catch` 当
   控制流。机械翻译会把实验债务一起搬进来。（详见 §D。）

工作量结论（多轮核查后维持）：真正需要新写的算法核心约 **1,600–2,200 行**；
AI 辅助下总工期 **16–26 人周**（§G 分解）。市场空窗（"现代、维护中、pip 可装、
带 GUI 的 Python stereo-DIC"）当前无人占据。

---

## B. 推荐的软件架构

### B.1 包布局

```
pyALDIC-3D/                      # 本仓库
└── src/al_dic_3d/
    ├── project/        # StereoProject、.aldic3d 会话包（沿用 2D 的 dedup-npz + json 信封设计）
    ├── calibration/    # CameraIntrinsics/StereoRig、6 格式导入器、undistort          [Qt-free]
    ├── sequence/       # StereoSequence：双 FrameProvider + 双掩膜流 + 配对校验        [Qt-free]
    ├── matching/       # CorrespondenceStrategy 协议 + 各策略实现 + 重采样工具        [Qt-free]
    │                   #   （策略设计见 02_correspondence_strategies.md）
    ├── reconstruct/    # 三角化(DLT)、重投影误差、世界系/试件系变换                    [Qt-free]
    ├── strain3d/       # 局部平面拟合 + 切平面应变、3D 平滑、3D 去外点                [Qt-free]
    ├── export/         # PLY/VTU/CSV/MAT/视频；复用 2D 的 LUT/二进制渲染原语          [Qt-free]
    ├── viz3d/          # pyvista/pyvistaqt 3D 场景（表面场 + 相机锥台 + 时间轴）
    ├── gui/            # MainWindow / AppState3D / controllers；导入 al_dic.gui 可复用 widget
    └── i18n/           # 自己的 .ts/.qm；运行时同时装载 al-dic 与 al-dic-3d 两套 QTranslator
```

### B.2 分层铁律

- `calibration/sequence/matching/reconstruct/strain3d/export` **禁止 import Qt**
  （包括 `al_dic.utils.locale_format`——已查明它 import Qt，属显示层辅助）。
- 整条计算链必须能在无头 CLI 下跑通（Phase 1 先于任何 GUI 的原因）。
- 重依赖（pyvista/VTK）置于 `al-dic-3d[viz3d]` optional extra，懒加载。
- GUI 只做编排与展示；业务状态在 `AppState3D`，计算结果对象全部 frozen dataclass。

### B.3 运行时数据流

```
StereoRig（标定，导入） ────────────────────────────┐
StereoSequence（双相机图像+掩膜流） ──┐              │
参考网格 mesh_L（左相机帧1，ROI→quadtree）│              │
                                     ▼              │
                  ┌──────────────────────────────┐  │
                  │ CorrespondenceStrategy（可插拔）│◄─┘（极线播种/QC）
                  │  · track_both（v1 默认=MATLAB 基线）
                  │  · stereo_each_frame / ref_direct（P2）
                  │  · adaptive（预留）             │
                  └──────────────┬───────────────┘
                                 ▼
                    CorrespondenceSet（每帧 xL, xR + quality + source）
                                 ▼
                undistort（点级）→ triangulate（DLT）→ Reconstruction3D（P^k, D^k, 重投影误差）
                                 ▼
                SurfaceMesh（参考构形） + StrainResult3D（平面拟合应变）
                                 ▼
                     viz3d / export / project(.aldic3d)
```

模块与用户点名的十项一一对应：project/data manager → `project/`；calibration module →
`calibration/`；stereo pair management → `sequence/`；2D DIC/matching backend →
`al_dic.core`（库）+ `matching/`（编排）；triangulation → `reconstruct/`；3D displacement
reconstruction → `reconstruct/`；surface strain → `strain3d/`；visualization →
`viz3d/` + 复用 2D 画布；export → `export/`；GUI controller → `gui/controllers`。

---

## C. pyALDIC-2D 复用清单（三档）

**首要原则（决策 D11）：2D 仓 `al-dic` 作为【只读的锁定版本库】消费——默认不改 2D 一行。**
Python 无强制私有，需要的 2D 内部直接 import；`al-dic` 版本锁死（当前 0.6.0），并在
`docs/DEPENDS_ON_2D.md` 维护"我们依赖了 2D 哪些内部"的清单，2D 将来重构时对照即可。
任何 2D 改动都是**下策**、**按需**、且**在单独的 2D 仓会话里**做——绝不在 3D 会话跨仓写、
更不在 Phase 0 预先做。

| 档位 | 内容 | 说明 |
|---|---|---|
| **原样 import（默认路径）** | `core/`（`run_aldic`、`FrameSchedule`、`DICPara`、`DICMesh`、累积变换）、`solver/`（含 `local_icgn`）、`mesh/`、`utils/`（插值/外点/geometry，**除 locale_format**）、`io/`（FrameProvider、图像加载）、i18n 基建模式与主题/图标、通用 widget（console_log、frame_navigator、image_list、collapsible_section、double_spin、info_icon、colorbar/range 系列）、导出渲染原语 | 引擎与平台件，**一行不改**；含"官方私有但可 import"的内部（锁版本消费） |
| **不复用，按模式重写（3D 侧新写）** | AppState → `AppState3D`、canvas_area（2088 行 2D 专用）、pipeline_controller、strain_window、`.aldic` 会话 schema（新 `.aldic3d`，沿用信封设计） | 这些是 2D 的业务逻辑，不是平台 |
| **延迟/可选的 2D 平台化 backlog（默认不做）** | 见下方"§C.1 延迟 backlog"。**每一条都不是 3D 的必做前置**，且都有 3D 侧替代做法 | 仅当"消费内部太脆"实际绊到时，才在 2D 会话里按需做并发小版本 |

### C.1 延迟的 2D 平台化 backlog（DO NOT DO preemptively）

以下 5 项曾被列为"Phase 0 缝隙"，现已降级——每项标注**触发时机**与**3D 侧替代**：

| # | 内容 | 3D 侧替代（默认走这个） | 何时才考虑真改 2D |
|---|---|---|---|
| ① 字段名注册表集中化 | 与 3D 无关（3D 有自己的字段名） | 纯 2D 内部整洁，永不为 3D 而做 |
| ② `admm_max_iter=0` 局部模式 | 走 ⑤ 的散点 `match_points`，不碰 ADMM；或临时用 `admm_max_iter=1` | 若确认 `=0` 崩溃且替代都不便时 |
| ③ 累积变换/插值提升为公开 API | 直接 import 2D 内部 + 锁版本；Phase 1 track_both 连调都不用调（`result_disp` 本就是累积量） | 若该内部被 2D 频繁重构、锁版本代价过高时 |
| ④ 解耦 widget（构造注入） | Phase 4 在 3D 侧适配/包装 2D widget | 若包装成本显著高于解耦时（Phase 4 再评） |
| ⑤ `match_points()` 散点局部 IC-GN | **3D 侧写薄 wrapper import `al_dic.solver.local_icgn`**（策略 S2/S3 的基础，见 02 §5.3） | 若薄 wrapper 需触碰过多 2D 私有细节时 |

2D 侧的 4 个超 800 行文件（canvas_area / export_dialog / app / strain_window）**不为 3D
项目而拆分**——它们属"不复用"档。

---

## D. MATLAB 3D-ALDIC 的使用方式

### D.1 信任清单（作为算法规格）

- `gui/runPipelineCore.m`（261 行）——**唯一可信入口**，最近整理过、无实验分支；
  其 8 步流程即移植蓝图：载图 → 归一化 → 载标定 → 帧1立体匹配 → 双相机时序匹配 →
  三角化重建 → 3D 应变 → 保存。
- `StereoMatch_STAQ.m`：跨相机匹配 = FFT 整像素搜索 + **仅局部** ICGN（tol=1e-3，
  无 ADMM），产出 `Coordinates_corr = 左网格坐标 + 视差`。
- `TemporalMatch_quadtree_ST1.m:463-489` 带 `FIX:` 注释的累积语义（在**变形后位置**
  插值增量）——inc 模式组合的 ground truth（历史 bug 的修复版）。
- `stereoReconstruction_quadtree.m`：先 undistort 点、后 DLT 三角化；左相机 = 世界系；
  逐帧重投影误差；**3D 位移 = 各帧三角化坐标 − 第 1 帧坐标**（模式无关）。
- 标定 5 格式转换器（`cameraParamsFormatConvertFrom*.m`，约 413 行纯解析）。
- `PlaneFit3_Quadtree.m` + `computeStrain3D.m`（53 行）+ `funSmoothDisp_3D.m` +
  `funRemoveOutliers3D.m` 的数学内容。
- `results/` 下 baseline `.mat` 与 Challenge 数据集——**数值验收锚点**。

### D.2 禁止照搬清单（附证据）

- 7 个 `TemporalMatch` 变体中的 6 个（`TemporalMatch/_inc/_inc_update_ROI/`
  `_inc_update_ROI_task2_1to8/_quadtree_acc_ST2/_ST2`，含一次性实验码）；
  `StereoMatch2`、`stereoReconstruction/_ST2/_inc` 等未被主线调用的变体——死代码。
- `RD` 结构的 4 套平行位移表示（`ResultDisp`/`_acc`/`_inc`/`_corr`）与 400 行
  模式×相机分支尾巴（`TemporalMatch_quadtree_ST1.m:393-493`）——被 `FrameSchedule`
  + 引擎内置累积变换**结构性取代**。
- 帧 2 调 β 后 `try/catch` 冻结复用（`:296-299`）、`isfield` 散布补默认、
  恒真条件 `ImgSeqNum <= ImgStartDataDrivenMode`（`:38,108`）、`showImgOrNot` 调试图。
- `ba_interp2` MEX（2D 已用 numba/`map_coordinates` 等效替代）；
  `scatteredInterpolant` 用 2D 现成插值工具替代。
- 函数名拼写错误一并消失（`organizeMatchedPairds` → 正名）。

### D.3 acc/inc 语义理清（正式契约）

设材料点 = 左相机第 1 帧网格节点 X_L；帧 1 立体匹配给出对应点 X_R = X_L + d(X_L)。
下游唯一需要的是**每帧两组像素位置**：

```
x_L^k = X_L + U_L^k(X_L)        x_R^k = X_R + U_R^k(X_R)      （U 均为累积位移）
```

两种模式只是产生 U 的方式不同：

- **acc（总体拉格朗日）**：每帧直接对参考帧求解，U^k 天然是累积量。无组合误差；
  大变形退相关时失效。
- **inc（更新拉格朗日）**：对 k−1 帧求解增量 u^k（定义在 k−1 帧的欧拉网格上），
  累积必须按

  ```
  U^k(X) = U^{k−1}(X) + u^k( X + U^{k−1}(X) )
  ```

  组合——**增量场必须在当前变形位置取值**。MATLAB 当年的 bug 即在参考位置取值，
  `FIX:` 注释是修复痕迹。pyALDIC-2D 的 `_compute_cumulative_displacements_tree`
  已实现正确组合（且泛化到任意参考树）。

**三条铁律**（从 MATLAB 的教训提炼）：

1. 模式复杂度**全部**封在 2D 追踪层内；三角化与应变只消费 `CorrespondenceSet`
   （每帧位置表），永远模式无关（`stereoReconstruction_quadtree.m:24-26` 的
   `D = P^k − P^1` 已证明这天然成立）。
2. 每个参考帧的网格**只建一次并缓存**。MATLAB 每帧重跑 FFT + 重建 quadtree
   （`:108` 条件恒真），acc 分支却假设网格与帧 2 一致——若细化结构随 U0 漂移会
   静默错位（**已识别隐患**）。Python 侧因 2D 引擎"每参考建一次 + mask-hash 失效"
   而结构性免疫；移植时不得复制"每帧重建"行为。
3. 配对关系提升为数据（`FrameSchedule`），组合收敛为独立变换阶段——分支消失，
   acc/inc 成为同一段代码的两组输入。

### D.4 提取方法论

读 MATLAB 时按"主线优先"：从 `runPipelineCore.m` 顺藤摸瓜，只读它调用的函数；
遇到同名多变体一律以主线调用者为准。数值验证用 `results/` baseline 与
`Stereo_DIC_Challenge_2.1_Bespoke` 数据做同输入对位，**先对齐中间量**（视差场 →
2D 位移场 → 三角化坐标 → 应变）再看端到端。坐标约定（MATLAB 图像按 (x=行) 索引
并转置显示 vs numpy (row,col) vs 内参 K 的 (u=列,v=行)）是头号静默杀手——Phase 1
第一件事是写 `COORDINATES.md` + 往返测试。

---

## E. 核心数据结构与接口

全部 frozen dataclass（不可变）；NaN = 无效点并沿链传播；数组 float64。
N 相机就绪（dict + 显式外参对），v1 只实现 ("L","R")。

```python
CameraIntrinsics    # fx fy cx cy skew + 畸变(k1 k2 k3 p1 p2)，格式无关规范化构造
StereoRig           # cameras: dict[str, CameraIntrinsics]
                    # extrinsics: dict[tuple[str,str], tuple[R(3,3), T(3,)]]
                    # 约定：cam "L" 为世界系（R=I, T=0）
StereoSequence      # providers: dict[str, FrameProvider]（复用 2D 协议）+ 掩膜流 + 配对校验
DisparityField      # 某一帧的跨相机匹配结果：frame_idx + left_pts(n,2) + d(n,2)
                    #   + znssd(n,) + valid(n,)   （不再假设只属于帧 1——策略 2 需要逐帧）
CorrespondenceSet   # ★ 中心契约（策略无关、模式无关）：
                    #   strategy: str
                    #   xL, xR: (n_frames, n_pts, 2)   每帧位置，NaN=无效
                    #   quality: (n_frames, n_pts)     ZNSSD
                    #   source:  (n_frames, n_pts) u8  0=TRACKED 1=STEREO_REFRESH 2=RESCUED 3=INVALID
DICResult2D         = al_dic.PipelineResult 原样复用（result_disp 已是累积位移）
Reconstruction3D    # P(n_frames,n,3), D = P − P[0], reproj_err(n_frames,n)
SurfaceMesh         # 拓扑 = 左 quadtree 网格 elements；节点 = P[0]（参考构形）
StrainResult3D      # 每帧 εxx εyy εxy ε₁ ε₂ γmax vonMises dwdx dwdy + coefficients + void_index
StereoProject       # 以上全部 + Correspondence3DConfig + 双 DICPara + 出处元数据 → .aldic3d
```

对应策略接口（详细设计与四种实现见 `02_correspondence_strategies.md` §5）：

```python
class CorrespondenceStrategy(Protocol):
    name: ClassVar[str]                    # 注册表 token
    def compute(self, seq: StereoSequence, rig: StereoRig, mesh_L: DICMesh,
                cfg: CorrespondenceConfig,
                progress=None, stop=None) -> CorrespondenceSet: ...
```

关系链：`StereoRig + StereoSequence + mesh_L → [CorrespondenceStrategy] →
CorrespondenceSet → Reconstruction3D → StrainResult3D`。

**`CorrespondenceSet` 是整个设计的隔离墙**：上游吸收全部策略/模式复杂度
（acc/inc、参考调度、重采样、重锚、救援），下游只看"每帧位置"。守住这面墙，
3D 代码不会重演 MATLAB 的分支增殖，未来新增策略也不触碰下游。

---

## F. GUI workflow 设计

与 2D 同一套 UX 语法（左侧工作流步骤、中央画布多标签、右侧参数栏、底部控制台），
用户从 2D 迁移零学习成本；但外壳、状态、控制器均为 3D 自有实现。

1. **New/Open Project** — `.aldic3d` 会话，双击关联，续载直达原页面（沿用 2D 已验证方案）；
2. **Import L/R sequences** — 双图像列表（复用 `image_list`），自动配对校验
   （数量/尺寸/文件名模式），错配即时红标；
3. **Calibration** — 六格式导入向导 + 立即质检页：内外参摘要、基线距、极线几何叠加
   预览——**标定错误必须死在这一步**；
4. **ROI** — 左相机帧 1 上绘制，复用 2D 全套 ROI 工具（circle3、掩膜导入、批量 ROI）；
5. **Correspondence 设置与预检** — 策略下拉（默认 `track_both`）+ 各策略参数子面板；
   单独按钮先跑帧 1 立体匹配，显示视差场 + ZNSSD 质量图，提交全量计算前暴露退相关
   区域（MATLAB 版没有的纯 UX 增益）；
6. **Run** — acc/inc 语义复用 2D workflow 面板；进度分段（对应策略各阶段 + 三角化 +
   应变），可取消；
7. **Results** — 三组标签页：每相机 2D 场（复用 2D 画布）、**3D 视图**（pyvista：
   变形表面 + 标量着色 + 相机锥台 + 时间轴播放）、应变场；QC 子页显示逐点
   quality/source 图与"重投影误差 vs 帧号"曲线（漂移监视器）；
8. **Export** — PLY/VTU（ParaView 生态）、CSV/MAT、截图/动画（复用 2D 导出管线的
   分辨率预设与流式动画）。

语言切换（8 语种契约）与会话保存从第一天按 2D 契约执行，不是收尾补丁。

---

## G. 分阶段开发路线

| 阶段 | 目标 | 输入 | 输出 | 验证（门禁） | 主要风险 |
|---|---|---|---|---|---|
| **P0**（~1 周） | 3D 仓脚手架（**不碰 2D**） | pyALDIC（只读锁定） | 本仓 src 布局/pyproject（`al-dic==0.6.*` editable）/CI/pre-commit/`git init`；CLAUDE.md 已就位 | 3D CI 绿（`import al_dic_3d` + `al-dic-3d --help` + 空测试） | 无（不动 2D 即无回归风险） |
| **P1**（3–5 周） | 无头立体 MVP：策略接口 + `track_both`（仅 acc） | P0 + MATLAB baseline.mat + 标定文件 | calibration/sequence/matching(接口+S1)/reconstruct + CLI + `COORDINATES.md` | ① 三角化合成几何闭环（µm 级）；② MATLAB 对位：2D 场 ≤1e-6 px、3D 坐标 µm 量级；③ Challenge 样例；④ PDF 报告 | 坐标约定（往返测试灭杀）；大视差 FFT 钳制（视差先验 offset + 极线播种） |
| **P2**（3–4 周） | inc 模式 + 策略 2/3 + 鲁棒性 | P1 | inc 路径；`stereo_each_frame`、`ref_direct` 实现；三策略对比 harness；3D 去外点 + 重投影 QC 门；合成双目真值生成器 | acc/inc 自洽（小变形差<噪声底）；MATLAB inc 对位；**三策略对比 PDF**（漂移曲线/噪声底/存活率，见 02 §6） | 累积组合语义（对照 `FIX:` 行实现+测试）；合成器需投影一致性 |
| **P3**（2–3 周） | 3D 表面应变 | P2 | strain3d（先写 `strain3d_math.md` 再实现） | 解析场测试（刚体旋转→零应变；平面/圆柱/球面已知应变）；MATLAB strainPerFrame 对位；VSG 敏感性入报告 | 与 `computeStrain3D` 定义对齐 |
| **P4**（4–6 周） | GUI alpha | P1–P3 | 外壳、8 步工作流、pyvista 标签页、QC 页、会话保存 | 全流程冒烟；会话往返；伪语言扫描（⟦…⟧）通过 | pyvista 大网格性能（decimation 预案）；内存 2× 双流（先落实 2D 内存清单 3–7 项） |
| **P5**（3–5 周） | 产品化 | P4 | 导出全家桶、i18n 8 语种 100%、用户手册、PyPI 发布 | i18n stats 全绿；Challenge 2.0 验证；手册随版编译 | 收尾膨胀——按 2D v0.6.0 发布清单执行 |

**总计 16–26 周（AI 辅助口径）。** 两条纪律：门禁不过不进下期；每期产出可视化 PDF
报告（matplotlib PdfPages，存 `reports/`）。

---

## 附录：已验证证据索引（file:line）

**pyALDIC-2D（`../pyALDIC/src/al_dic/`）**

| 论断 | 证据 |
|---|---|
| `run_aldic` 接受外部 mesh/U0/compute_strain | `core/pipeline.py:551-560` |
| 给 mesh+U0 即跳过 FFT | `core/pipeline.py:887` `need_fft = dic_mesh is None or current_U0 is None` |
| 增量→累积树状变换（含变形位置插值） | `core/pipeline.py:417 _compute_cumulative_displacements_tree`、`:507`、`:1517-1537` |
| FrameSchedule 泛化 acc/inc | `core/data_structures.py:52-111`（`from_mode`、every-n） |
| 2 分量交错布局深度固化（勿泛化为 3 分量） | `solver/subpb2_solver.py:83` `fem_size = 2*n_nodes`、`:221-223` `kron(K8, I_2)` |
| ADMM 迭代数可调（local-only 的基础） | `core/data_structures.py:335` `admm_max_iter: int = 3` |
| 计算层 Qt-free；例外仅两个显示辅助 | 全库 Qt import 44 文件皆在 `gui/`，另 `i18n/__init__.py`、`utils/locale_format.py` |

**MATLAB（`../3D-Stereo-ALDIC/`）**

| 论断 | 证据 |
|---|---|
| 8 步流水线规格 | `gui/runPipelineCore.m`（261 行） |
| 标定仅导入（5 格式） | `gui/runPipelineCore.m:251-261 loadCalibration` switch |
| 跨相机匹配 = FFT + 仅局部 ICGN | `func/StereoMatch_STAQ.m`（无 ADMM；tol=1e-3） |
| inc 累积须在变形位置插值（修复版） | `func/TemporalMatch_quadtree_ST1.m:463-489`（`FIX:` 注释） |
| 3D 位移模式无关（P^k − P^1） | `func_quadtree/stereoReconstruction_quadtree.m:24-26` |
| 左相机 = 世界系 | 同上 `:5-8` |
| TemporalMatch 变体爆炸（7 个 3,745 行，主线只用 1 个） | `func/TemporalMatch*.m` 清单 |
| `epipolar_ICGN1` 不在主线（仅 `StereoMatch2.m` 调用；固定平移的 ZNSSD 打分器） | grep 全库调用点 |
| 新算法核心体量 ≈1.6–2.0k 行 | 立体专属 .m 毛计 ~3.95k，扣除绘图 ~760、读图 ~750、格式转换 ~413 |

**第三方实现（策略印证，详见 02 §4）**

| 实现 | 策略 | 证据 |
|---|---|---|
| 3D-Stereo-ALDIC（本项目 MATLAB 版） | S1 track_both | `runPipelineCore.m:74-93` |
| ADIC3D（Atkinson & Becker） | S1 + 时序参考方式参数化（`RefStrat`） | `ADIC3D-main/ADIC3D.m:20-25` |
| MultiDIC（Solav et al.） | S3 ref_direct（2n 张图统一以 cam1 帧 1 为参考） | `MultiDIC-1.1.0/main_scripts/STEP2_2DDICusingNcorr.m:1-7` |

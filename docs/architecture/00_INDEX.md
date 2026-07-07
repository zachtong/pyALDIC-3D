# pyALDIC-3D 架构文档索引与决策日志

> 本目录是 pyALDIC-3D 的**架构基准（architecture baseline）**。所有后续开发会话
> （无论由哪个模型执行）都应以本目录为准绳；与文档冲突的实现需先修订文档再动代码。

## 仓库位置（Repository locations）

> 这三个仓库是**兄弟目录**（同一个 `MATLABCodes/` 父目录下）。跨机器时绝对路径前缀
> 可能变化（用户有多台机器，用户名 `13014` 在别的机器上可能不同），**以"兄弟关系"
> 为准，不要死记绝对路径**。新的开发会话应把工作目录设在 `pyALDIC-3D` 文件夹，
> 这样文档里的 `../pyALDIC`、`../3D-Stereo-ALDIC` 相对路径可直接解析。

| 仓库 | 相对本工作区 | 角色 | GitHub（兜底） |
|---|---|---|---|
| pyALDIC-3D | `.`（工作区） | 本项目（import `al_dic_3d` / PyPI `al-dic-3d`） | 尚未创建（Phase 0 `git init`） |
| pyALDIC | `../pyALDIC` | 2D 平台，**只读锁定库依赖 `al-dic==0.6.*`**（默认零改动，D11） | `github.com/zachtong/pyALDIC` |
| 3D-Stereo-ALDIC | `../3D-Stereo-ALDIC` | MATLAB 算法参考（只读） | `github.com/zachtong/3D-Stereo-ALDIC`（upstream: YangMechanicsGroupUTAustin） |

绝对路径（author 机器，2026-07-02，仅供定向）：
`C:\Users\13014\OneDrive - The University of Texas at Austin\Documents\MATLABCodes\{pyALDIC-3D,pyALDIC,3D-Stereo-ALDIC}`。
自检：会话开始时 `ls ..` 确认两个兄弟目录都在；缺失则从上面 GitHub clone 到兄弟位置，
**没有参考仓不要开工**。

## 阅读顺序

1. `01_technical_baseline.md` — 技术基线（总体判断 → 架构 → 复用清单 → MATLAB 使用方式 → 数据结构 → GUI → 分期路线）
2. `02_correspondence_strategies.md` — 立体/时序对应策略调研与可插拔设计（01 的 §E/§G 引用此文档）
3. `03_opus_phase_prompts.md` — 分阶段执行指令（开发会话的入口文件）

## 决策日志（Decision Log）

| # | 日期 | 决策 | 依据 |
|---|---|---|---|
| D1 | 2026-07-02 | pyALDIC-3D 是**独立应用程序**（独立仓库/文件夹、独立 project schema、独立状态管理与工作流控制器、独立 3D 可视化层），构建在 al-dic 平台之上；**不是** 2D 软件内部的一个 3D 模式 | 用户决策；2D 主线零风险；Part-2 论文需要独立 repo/DOI |
| D2 | 2026-07-02 | 标定 = **仅导入**（MatlabCV/MatchID/MMC/DICe/OpenCorr/OpenCV-YAML 六格式），原生标定推迟到 v2 | MATLAB 先例：`runPipelineCore.m:251-261` 本就 import-only 且已过同行评审；最大精度风险移出 MVP |
| D3 | 2026-07-02 | 3D 渲染 = **pyvista/VTK**，置于 `[viz3d]` optional extra 之后，懒加载 | 科学表面场渲染事实标准；pyqtgraph-GL 3D 能力不足 |
| D4 | 2026-07-02 | 数据结构 **N 相机就绪**（相机 dict + 显式 (i,j) 外参对），v1 只实现双相机 | 设计期成本≈0，事后改造成本极高；对齐 MultiDIC 的多相机能力预期 |
| D5 | 2026-07-02 | 立体/时序对应策略 = **可插拔组件**（`CorrespondenceStrategy` 协议 + 注册表）。v1 默认 `track_both`（=MATLAB 基线，对位锚点）；`stereo_each_frame` 与 `ref_direct` 在 Phase 2 落地并做三策略对比；`adaptive` 预留 post-v1 | 用户要求；详见 `02_correspondence_strategies.md` |
| D6 | 2026-07-02 | 世界坐标系 = 左相机（R=I, T=0）；试件坐标系变换作为后处理步骤 | MATLAB 约定（`stereoReconstruction_quadtree.m:5-8`），验证对位需要 |
| D7 | 2026-07-02 | 匹配在**原始（未校正 rectify）图像**上进行；undistort 只在三角化前作用于点坐标；极线几何仅用于搜索播种与 QC | 避免重采样损伤散斑；与 MATLAB 参考一致；见 02 §5.4 |
| D8 | 2026-07-02 | 命名：**PyPI 发布名 `al-dic-3d`，import 包名 `al_dic_3d`**（src 布局 `src/al_dic_3d/`，CLI console-script `al-dic-3d`，等价 `python -m al_dic_3d`）；会话文件扩展名维持 `.aldic3d` | 用户拍板（原 Q1）：延续 PyPI 上 2D 包 `al-dic` 的命名族系 |
| D9 | 2026-07-02（2026-07-02 澄清修订） | pyALDIC-3D 有**自己独立的学术身份**，与 2D **不共用、不挂靠**：① 自己的 **Zenodo 记录 → 自己的 concept DOI**（独立于 2D 的 concept DOI `19521061`），每次发版铸自己的 version DOI；② 自己独立的 **SoftwareX 文章**（"Part 2" 是一篇 standalone article、有自己的 paper DOI，**不是** 2D 论文的续章/附录，仅在引言里 cite 2D 作为前作）。许可证**类型**可沿用 2D（GPL 等，许可 ≠ DOI）。验证/示例材料从 P2 起按 SoftwareX 体例积累 | 用户拍板（原 Q2）+ 用户澄清：独立应用 → 独立 DOI + 独立论文 |
| D10 | 2026-07-02 | N 相机（>2）= **post-v1**；v1 数据结构 N 相机就绪（相机 dict + (i,j) 外参对）但只实现双目 | 用户拍板（原 Q3），确认 D4 默认方案 |
| D11 | 2026-07-02 | **2D 仓 `al-dic` 作为【只读锁定库】消费——默认零改动。** 撤销原"Phase 0A 改 2D 5 条缝"；那 5 项降级为 §C.1 的**延迟可选 backlog**，每项有 3D 侧替代（多为 import 2D 内部 + 锁版本），仅在将来真被绊到时于**单独的 2D 会话**里按需做，绝不在 3D 会话跨仓写。3D 侧维护 `docs/DEPENDS_ON_2D.md` 耦合清单；`al-dic==0.6.*` 锁定。Phase 0 = 仅脚手架 | 用户质询"2D 为何要写权限"→ 库消费者本不应改库；保护成熟的 2D 主线、缩小范围与风险 |
| D12 | 2026-07-07 | **修订 D2：新增原生内置标定，成为标定步骤的主入口**；六格式导入降为备选；手动参数输入为兜底。技术底座 = 纯 OpenCV（`opencv-python-headless>=4.7` 既有依赖，零新增二进制依赖）：棋盘格 `findChessboardCornersSB(WithMeta)`、ChArUco 4.7+ OO API（`CharucoDetector.detectBoard`+`matchImagePoints`）、圆点板 `findCirclesGrid` + **三同心定位圆编码靶自研检测器**（用户实际靶型）；单目 `calibrateCameraExtended`（家用打印板可选 RO 法）→ 立体 `stereoCalibrateExtended`（默认 `CALIB_FIX_INTRINSIC`，联合精化为高级选项）+ 坏图剔除循环（k·中位数）+ 极线距离验证。产物 = `StereoRig` 写出 `opencv_yaml`（含出处元数据节点）回流既有 `calibration_file` 路径——RunConfig/runner/session schema v1 **零改动**。QC（逐图误差柱+阈值剔除重标+覆盖率/位姿多样性诊断）为对 MATLAB 参考（仅打印 frame-1 误差、无门禁）的明确超越点 | 用户 2026-07-07 拍板（靶型=棋盘+编码圆点靶；范围 C1+C2 一次做完）；5 路调研 workflow（OpenCV SOTA / DIC 领域 / 第三方库 / 本仓接入点 / MATLAB 约定）44 条关键事实 42 条对抗核查确认：mrcal/Kalibr/MC-Calib/PyBoof 平台不可用、multical LGPL 不可移植；OpenCV 本体覆盖全部所需；aniposelib(BSD-2) 联合光束平差留作后续移植候选 |

## 开放问题

（2026-07-02：Q1–Q3 已全部由用户拍板关闭，答案见决策日志 D8–D10。当前无开放问题。）

## 阶段交接协议（Handoff Protocol）

- **一个阶段一个开发会话**。仓库根的 **`CLAUDE.md` 会被 Claude Code 自动加载**（内含
  Master Preamble：身份/仓库位置/不变量/工程规则），所以会话开头**只需粘贴 `03` 里
  对应的 Phase Prompt**；不用再粘贴 Preamble。（非 Claude-Code harness / API 调用时，
  才需要连 Preamble 一起贴。）
- **所有阶段都在本仓工作区做，不改 2D 仓**（决策 D11：2D 作为只读锁定库消费）。
  两个参考仓（`../pyALDIC`、`../3D-Stereo-ALDIC`）全程**只读**——`.claude/settings.json`
  已 deny 对它们的写。Phase 0 = 仅搭 3D 脚手架，无任何跨仓写。
- 每阶段结束条件（门禁）：该阶段测试全绿 + 规定的对位/验证指标达标 + `reports/` 下的
  可视化 PDF 报告 + 用户确认。**门禁不过不得进入下一阶段。**
- 每阶段结束时必须更新本文件的 Changelog，并将新产生的决策补入决策日志。
- 文档与代码冲突时：**文档优先**；确需偏离，先在此登记决策再改代码。

## Changelog

- 2026-07-07 v1.4.1 — **内置标定（D12）C1+C2 实施完成，五门禁全 PASS**（`main` 至
  `60bb641`，178 tests green）。计算层 `calibration/boards|detect|solve|report`（纯 OpenCV，
  Qt-free）：四板型检测（棋盘 SB+cornerSubPix 精化、ChArUco 4.7 OO API、圆点阵列、**编码圆点靶
  自研检测器**：轮廓层级找三环形定位圆→仿射假设打分→单应格点精化，支持部分出视场+触边点剔除）；
  求解（默认 zero-tangent[平面靶 cx↔p1p2 耦合实测放大噪声 3 倍]+FIX_INTRINSIC，联合精化/RO 法/
  切向可选，坏图对剔除循环带 1px 绝对下限，极线验证，**圆点偏心解析修正**）；`to_opencv_yaml`
  回流既有导入漏斗。合成 parity 门禁（tests/synth_calib.py 精确逆投影渲染 + 18 覆盖设计位姿）：
  棋盘 rms 0.014px / fx 0.003% / cx 0.07px / 基线 1.8µm / R 0.002°；编码靶 18/18 对 rms 0.036px；
  切向恢复分毫不差。CLI `al-dic-3d calibrate`。GUI：标定对话框（逐对状态表+误差条形图+阈值剔除
  重标+QThread）与手动参数对话框，左栏三入口（内置主/导入备/手动兜底）。i18n 191 串 ×7 语种
  100%。`reports/calib_builtin.pdf`（tools/calib_report.py 自校验）。待办：真实编码靶照片调参。
- 2026-07-07 v1.4.0 — **立项内置标定（D12，修订 D2）**：5 路并行调研 workflow + 对抗核查（44 条
  关键事实 42 条确认）确定纯 OpenCV 底座；三层入口（内置标定主 / 六格式导入备 / 手动参数兜底），
  三者统一收敛为 `StereoRig`→`opencv_yaml`→既有质检漏斗；靶型 = 棋盘格 + ChArUco + 编码圆点靶
  （三同心定位圆，用户靶型，自研检测器）；范围 C1+C2 一次实施（boards/detect/solve/report 计算层
  + 合成 parity 门禁 + CLI `calibrate` + 标定/手动两对话框 + i18n）。同步修订 01 §B.1 与 §F 步骤 3。
  实施计划 `tasks/todo.md`。
- 2026-07-07 v1.3.6 — **Phase 4 GUI 重建为 pyALDIC 同款 + 四门禁全过**（`main` 至 `6a3592e`，146 tests
  green）。深研 2D 前端源码（app/panels/window_chrome/theme/icons/widgets）+ `assets/` 参考截图后，
  **废除分页式 8 步工作流**，重建为 pyALDIC 单窗三栏语法：左侧栏 320px（双相机拖放导入+配对表+标定
  实时质检+策略/模式+ROI 画布绘制+参数，复用 2D CollapsibleSection/区段头/badge 范式）、中央画布
  （工具条+分层缩放画布+配置卡+复用 2D ColorbarOverlay+播放条；结果=追踪点 colormap 散点，跨帧稳定
  色域；**3D View 切换**=pyvista 曲面+相机锥台，lazy 降级）、右侧栏 280px（Run 3D Analysis btn-primary
  +Cancel btn-danger+Export 对话框+进度/已用/剩余+FIELD U/V/W/|D|+应变网格+相机切换+可视化+日志）。
  后端不变（WorkflowController/ProjectDraft/RunResult，3D-DIC 逻辑）；`GuiSignals` 信号枢纽替代 2D
  AppState 单例。**离屏截图自检环**（tools/gui_screenshot.py，QT_QPA_FONTDIR 修 tofu）3 轮迭代对齐
  assets/main_page.png。Export 对话框（格式+字段选择）+ Qt-free `export/tables.py`（npz/mat/逐帧 CSV）。
  **i18n 契约完成**：118 串 ×8 语言 100% 填充（术语对齐 2D 目录）、.qm 编译入库、运行时加载验证
  （zh_CN 截图实证）、tools/fill_translations.py 自校验。**四门禁全过**（session round-trip / i18n scan+
  8 locale 100% / full-workflow smoke / phase4_gui.pdf，自校验报告）。pyvista 已装（[viz3d]）；GL 渲染
  待有显示机器目检。**未进入 Phase 5。**
- 2026-07-03 v1.3.5 — **Phase 4 GUI 可验证基础层**（`main` 至 `d1136c7`，128 tests green）。在无显示环境
  里完成全部**可测**部分（交互式 GUI 与 pyvista 需在有显示的机器上可视化迭代）：`project/`——`AppState3D`
  + `.aldic3d` 会话 save/load（版本化 zip：session.json 配置/视图 + results.npz 结果，含 strain），**session
  round-trip 门禁达成**；`gui/`——`WorkflowController`（Qt-free 8 步工作流逻辑，headless 跑通 config→run→
  results→会话往返）+ `MainWindow3D` 外壳 + 8 页骨架（全 `self.tr()` 字面量）+ `al-dic-3d gui` 入口；
  `i18n/`——AST 静态扫描（**pseudo-locale-clean 门禁达成**，`tools/i18n.py scan`）+ `install_translators`
  + lupdate/lrelease 工具链（`tools/i18n.py extract/compile`）。offscreen 冒烟测试验证 MainWindow 构造+走 8 步。
  **4 门禁：session round-trip ✅ / pseudo-locale ✅ / full-workflow smoke（headless 骨架 ✅，完整 UI 待显示）
  / phase4_gui.pdf ⏳**。**剩余待显示机器可视化迭代**：页面填充 2D widgets、pyvista 3D tab、8 语言 .ts/.qm
  填充（字符串定稿后）、走查 PDF。**未进入 Phase 5。**
- 2026-07-03 v1.3.4 — **Phase 3 3D 表面应变完成**（`main` 至 `00a40d9`，114 tests green）：
  先按规约写 `docs/strain3d_math.md`（从 `PlaneFit3_Quadtree.m`+`computeStrain3D.m`+`GetRTMatrix.m`
  提炼），再实现 `al_dic_3d.strain3d`（**纯 numpy/scipy，零新增 al_dic 依赖**）：局部 VSG 方窗邻域→
  切平面拟合→局部位移梯度→F=I+coef^T→E=½(FᵀF−I)→exx/eyy/exy/e1/e2/maxShear/vonMises/dwdx/dwdy；
  可选位移平滑 + specimen 变换（GetRTMatrix，凸包外最近邻兜底对齐 MATLAB 外推）。runner `[strain]`
  开关使 `al-dic-3d run` 产出 `strain_*`。门禁：**解析场全过**——刚体旋转→应变 5.5e-16、平面/柱面
  单轴拉伸→ε+ε²/2=0.0202（6 位精确）；`reports/phase3_strain.pdf`（解析门禁+非平面应变图+VSG 敏感性
  U 曲线，自校验，最优 strain_size=7）。对抗审查：核心数学零确认，1 条 specimen 凸包外解析差已修。
  **MATLAB strainPerFrame 对位仍延迟**（同 P1/P2，待用户数据集）。**未进入 Phase 4。**
- 2026-07-03 v1.3.3 — **Phase 2 对应层完成**（`main` 至 `3474b62`，105 tests green）：
  (1) inc 模式（`reference_mode` 贯通，引擎组合增量→累积；acc↔inc 自洽差 ~13µm < 噪声底）；
  (2) S2 `stereo_each_frame`（单左链 + 逐帧散点立体，warm-start，零重采样，source=STEREO_REFRESH）；
  (3) S3 `ref_direct`（左时序 acc + L1→R_k 直接跨匹配，链式播种，零漂移）；三策略均过合成 parity gate。
  (4) 鲁棒性：ZNSSD 门 + reproj 门 + 3D 通用外点检验（Westerweel-Scarano 思想），config `[quality]` 开关；
  (5) 非平面 Lagrangian 定点 warp 合成真值生成器（曲面 + 已知 3D 位移场，投影一致，反投影↔投影 <0.01px）；
  (6) 三策略对比 harness + `reports/phase2_strategies.pdf`（RMSE/漂移/噪声底/存活/reproj/变形 sweep/耗时，
  自校验，兼作 SoftwareX Part-2 材料）。策略差异符合 02 §2 预言：小变形 S3 最净、大变形 S3 先失效、S2 长序列胜。
  两轮对抗式审查（S2/S3/inc 零确认；一条 S3 种子链优化已采纳）。**MATLAB inc-baseline 对位仍延迟**（同 P1，
  待用户数据集）。**未进入 Phase 3。**
- 2026-07-03 v1.3.2 — **Phase 1 headless MVP 代码完成**（`main` 6 commits，末位 `f09a604`，
  87 tests green）：calibration/geometry(COORDINATES.md)/sequence/matching(TrackBoth S1，
  accumulative)/reconstruct(Reconstruction3D, D=P−P[0])/`al-dic-3d run config.toml`→.npz+.mat
  全部落地并端到端验证。Phase 1 门禁暂以**合成 parity gate** 达标：带真实镜头畸变的倾斜平面
  会聚立体场景 + 解析真值（单相 `cv2.remap` 渲染，零建模误差），驱动真实 `run_pipeline` 回收
  3D 位移中位 ~50µm / 2D 对应 ~0.04px / 重投影 ~5e-6px，`reports/phase1_report.pdf` 自校验
  （门禁不过即退出非零）。**真实 MATLAB-baseline 对位仍延迟**，待用户数据集后按真实数据重调
  容差闭合。TrackBoth 与 CLI 各经一轮对抗式多维审查（确认项已修）。**未进入 Phase 2。**
- 2026-07-02 v1.3.1 — 澄清 D9：pyALDIC-3D 的学术身份与 2D **完全独立**——自己的 Zenodo
  concept DOI（区别于 2D DOI 19521061）、自己独立的 SoftwareX 文章（"Part 2" 是 standalone
  article、自己的 paper DOI，仅 cite 2D 为前作）；Phase 5 加 CITATION.cff / DOI badge。
- 2026-07-02 v1.3 — **决策 D11：2D 仓改为只读锁定库消费，撤销 Phase 0A/2D 改动。**
  原"5 条平台缝"降级为 §C.1 延迟可选 backlog（每项有 3D 侧替代）；Phase 0 收敛为仅
  脚手架；`match_points` 由"2D 平台缝"改为 3D 侧薄 wrapper（02 §5.3）；新增
  `docs/DEPENDS_ON_2D.md` 耦合清单要求；`al-dic` 锁 `==0.6.*`。新增仓库根
  `.claude/settings.json`（两参考仓只读 + bash 白名单 + `rm -rf` deny）。
- 2026-07-02 v1.2 — 交接可用性：新增仓库根 `CLAUDE.md`（自动加载 Master Preamble，
  会话只需粘贴 Phase Prompt）；`03` 全部 prompt 块重排为**可直接复制**（去除句中人为
  换行）。（注：本条曾引入 Phase 0A/0B 拆分，已被 v1.3 的 D11 取代。）
- 2026-07-02 v1.1.1 — 用户拍板关闭 Q1–Q3 → 决策 D8–D10 入日志；全套文档的包名引用
  由默认值 `aldic3d` 统一改为 `al_dic_3d`（PyPI `al-dic-3d`）；Phase 2/5 prompt 补充
  SoftwareX Part-2 材料积累要求。
- 2026-07-02 v1.1 — 初始基线入库（由 pyALDIC 会话中的架构调研产出）。相对会话内 v1.0 的修订：
  (a) 明确"独立应用程序"定位（D1 措辞强化）；(b) 立体/时序对应策略从固定流程升级为
  可插拔组件（D5，新增文档 02）；(c) al-dic 平台缝隙从 4 条增至 5 条（新增 `match_points`
  散点局部 IC-GN 公开接口）；(d) Phase 2 扩容（含策略对比 harness），总工期 16–26 周。

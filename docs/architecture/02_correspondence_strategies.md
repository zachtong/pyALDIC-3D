# 立体/时序对应策略调研与可插拔设计（Correspondence Strategies）v1.0

> 本文档回应架构决策 D5（见 `00_INDEX.md`）：立体/时序匹配方案不硬编码为单一流程，
> 而是架构中的**可配置组件**。§1–§4 是调研（问题形式化、四种策略利弊、误差传播、
> 实现印证），§5–§7 是设计（接口、验证计划、默认建议）。

---

## 0. TL;DR

| 策略 | 一句话 | v1 地位 |
|---|---|---|
| S1 `track_both` | 帧 1 立体匹配一次，之后左右相机各自时序追踪 | **默认**（=MATLAB 基线，对位锚点），Phase 1 |
| S2 `stereo_each_frame` | 只在左相机时序追踪，每一帧都做左右立体匹配 | Phase 2；长序列/漂移敏感场景的推荐项 |
| S3 `ref_direct` | 所有左右图像全部直接对左相机帧 1 匹配 | Phase 2；小变形/短序列/计量精度场景 |
| S4 `adaptive` | 质量驱动的混合：主链 + 事件触发重锚 + 逐点救援 | post-v1；接口字段已预留 |

四种策略共享同一输出契约 `CorrespondenceSet`（每帧、每材料点在两相机中的像素位置
+ 质量 + 来源标记）。下游（三角化/应变/可视化/导出）对策略完全无感。

---

## 1. 问题形式化与记号

- 材料点：左相机帧 1 参考网格节点 **X_L**（n 个点，quadtree 网格承载拓扑）。
- 目标：对每帧 k = 1..N，获得这些材料点在两相机图像中的像素位置
  **x_L^k**、**x_R^k** → undistort → 三角化 P^k → 位移 D^k = P^k − P^1。
- 两类匹配算子及其误差性质：

| 算子 | 定义 | 误差来源 | 关键性质 |
|---|---|---|---|
| **T**（temporal） | 同相机、跨时刻相关 | 材料变形导致的退相关（随 \|k−ref\| 增长）、散斑退化 | 无视角差；acc/inc 由 `FrameSchedule` 表达；引擎原生支持 |
| **S**（spatial/stereo） | 跨相机、同时刻相关 | 视角差导致的透视畸变（由基线角决定，**不随时间变**）、左右光照差 | 无变形差（同一物理状态）；视差大但可由标定预估；一阶（仿射）形函数在中等基线角、局部近平面时够用 |
| **M**（cross，S3 专用） | 跨相机且跨时刻（L1→R_k） | 视角差 + 全部累积变形 + 散斑退化，同时吸收 | 最难的匹配；一阶形函数最先失效 |

- 误差记号：ε_T(k)（时序匹配误差）、ε_S（立体匹配误差）、ε_I（散点插值/重采样误差）、
  δ(k)（inc 组合的随机游走累积项）。三角化把像素误差放大为 3D 误差，深度方向放大
  系数 ~1/sin(基线角)。

---

## 2. 四种策略逐一分析

### S1 `track_both` — 帧 1 立体匹配 + 双相机时序追踪

**定义**：
```
d¹  = S(L1 → R1)                      在 X_L 处求视差 → X_R = X_L + d¹
U_L^k = T_L(1 → k)  （run_aldic 左序列，FrameSchedule 决定 acc/inc）
U_R^k = T_R(1 → k)  （run_aldic 右序列，同上；解在右相机自建网格上，
                       再重采样到对应点 X_R —— MATLAB 同款做法）
x_L^k = X_L + U_L^k        x_R^k = X_R + U_R^k(X_R)
```

**误差传播**：
- err(x_L^k) ≈ ε_T_L(k)；err(x_R^k) ≈ ε_S(帧1，**时间常量**) + ε_T_R(k) + ε_I(每帧重采样一次)。
- **关键性质：帧 1 立体误差是时间常量** → 它同时进入 P^k 与 P^1，在
  D^k = P^k − P^1 中一阶抵消 → **位移精度好于形貌精度**（绝对坐标保留该偏差）。
- **两条独立时序漂移链**（L 与 R）：inc 模式下各自随机游走 ~δ(k)·√k；两链互不
  约束，极线一致性无人维护 → 重投影误差随 k 增长，只能监控不能纠正。

**插值需求**：R 场→对应点重采样每帧 1 次（acc）；inc 模式两链各再加 1 次组合插值。

**成本**：1×S + 2(N−1)×T。最便宜；且唯一一次跨视角匹配发生在**未变形、散斑最完好**
的状态上——成功率最高。

**失效模式**：长序列漂移；某点在 R 视角中后期遮挡 → 即使 L 中仍可见也丢点，无救援。

**适用**：默认与基线对位；中等长度序列、中等变形；需要与 MATLAB/已发表结果严格
对齐的一切场合。

### S2 `stereo_each_frame` — 左相机时序 + 每帧立体匹配

**定义**：
```
U_L^k = T_L(1 → k)                     x_L^k = X_L + U_L^k     （唯一时序链）
d^k  = S(L_k → R_k)  在散点 x_L^k 处求值（warm-start：d^{k−1} + 左侧运动预测）
x_R^k = x_L^k + d^k
```

**误差传播**：
- err(x_R^k) ≈ err(x_L^k) + ε_S(k)。ε_S(k) 逐帧**新鲜**、不累积；左链误差是
  两相机共模（它只移动 d^k 的求值点，经 ∇d·ε 进入，视差场平滑时是二阶小量）。
- **单漂移链**；每帧满足极线约束 → 重投影误差恒处匹配噪声水平，成为**真正的
  QC 信号**（S1 中它混入漂移，信号失真）。
- 代价：ε_S(k) 在 k 与 1 之间不相关 → 在 D^k 中**不抵消**，表现为 3D 位移的
  白噪声（√2·σ_S 量级）——比 S1 的（可抵消的）立体偏差略吵，但无漂移项。
- 长序列交叉点：S1 总误差 ~ 双链漂移增长；S2 ~ 单链漂移 + 恒定噪声。k 大时 S2 胜。

**插值需求**：若用"网格解 + 插值到散点"则每帧 1 次 ε_I；**推荐**改用散点局部
IC-GN（3D 侧 `match_points` 原语，见 §5.3）直接在 x_L^k 处求解 → 零插值。

**成本**：(N−1)×T + N×S。S 有 d^{k−1} warm-start 后开销接近 T → 总量与 S1 相当。
每帧立体匹配面对的视角差恒定（不随变形恶化，除非表面转离某相机造成局部遮挡/
透视加剧）。

**失效模式**：表面大角度偏转区域的立体匹配退化；每帧立体噪声进入位移谱
（可后置时域平滑缓解）。

**适用**：长序列、漂移敏感、遮挡频发、需要逐帧质量门控的工业化场景。

### S3 `ref_direct` — 全部直接对左相机帧 1 匹配

**定义**：
```
U_L^k = T_L(1 → k)（acc 强制）          x_L^k = X_L + U_L^k
m^k  = M(L1 → R_k)                      x_R^k = X_L + m^k
（初值可用 m^{k−1} 链式播种——播种链 ≠ 误差链：播种失败只影响收敛速度/成功率，
  不把误差传给下一帧）
```

**误差传播**：err(x_R^k) = ε_M(k)，单次匹配、无组合、无插值 → **零漂移、零 ε_I**，
每帧误差独立。这是三者中误差结构最干净的。

**代价**：M 是最难匹配——视角差 + 全部累积变形一次吸收。一阶形函数最先到极限
（二阶形函数可显著续命，见 §5.5 引擎扩展 E2）；变形越大失败率越高，失败即丢点
（除非配 S4 救援）。**它把"匹配难度"作为变形的增函数——恰在你最需要 DIC 的
大变形时刻失效**，这是它作为通用默认的根本障碍。

**成本**：(N−1)×T + (N−1)×M_hard（M 迭代多、重试多）。

**适用**：小变形、短序列、形貌/位移计量级精度需求（零漂移最重要时）；
MultiDIC 正是此策略（见 §4），其文档也将适用域限定在中等变形。

### S4 `adaptive` — 质量驱动混合（post-v1，架构预留）

**组合原语**（可按需启用）：
- 主链 = S1（最便宜）；
- **事件/周期触发重锚**：当某点重投影误差或 ZNSSD 超阈值，或每 M 帧例行，
  在该帧局部重做立体匹配（= 局部切换 S2），消灭漂移；
- **逐点救援**：时序链丢点后用当前帧立体匹配找回（source=RESCUED）；
- **重锚衔接**：重锚引入的新偏差与旧链偏差不同 → 3D 位移时间序列会跳变；
  需在重锚帧做偏差桥接（blend 或双解重叠段），否则 QC 曲线好看、位移曲线难看。

**风险**：切换不连续、簿记复杂、验证组合爆炸。**v1 不实现**；架构要求仅两条：
`CorrespondenceSet` 携带逐点 `source`/`quality` 字段（已定义），策略实现可组合
调用彼此的原语（注册表 + 纯函数式原语层已满足）。

---

## 3. 对比矩阵

| 维度 | S1 track_both | S2 stereo_each_frame | S3 ref_direct | S4 adaptive |
|---|---|---|---|---|
| 时序漂移链数 | **2**（L+R 独立） | **1**（仅 L） | **0** | ≤1（受控） |
| 每帧新增噪声 | 低 | 中（ε_S 不抵消） | 中高（ε_M） | 低–中 |
| 立体偏差在位移中抵消 | **是**（时间常量） | 否 | 否 | 部分 |
| 极线一致性维护 | 无（仅监控） | **每帧** | 每帧 | 事件驱动 |
| 遮挡鲁棒/丢点救援 | 弱 | 中（逐帧可检） | 弱 | **强** |
| 散点插值次数/帧 | 1（acc）–3（inc） | 0（用 match_points） | **0** | 视组合 |
| 跨视角匹配难度 | 一次、最易（未变形态） | 恒定（视角差固定） | **随变形增长** | 混合 |
| 计算量（N 帧） | 1S+2(N−1)T（**最低**） | (N−1)T+N·S(warm) | (N−1)T+(N−1)M_hard | S1+增量 |
| 大变形适应性 | 好（inc 时序扛） | 好 | **差** | 最好 |
| 长序列适应性 | 中（双链漂移） | **好** | 好（若变形小） | 最好 |
| MATLAB 基线对位 | **是** | 否 | 否 | 否 |
| 实现复杂度 | 低（引擎直用） | 中（需 match_points） | 低–中 | 高 |

**没有全局最优**——这正是可插拔的理由：S1 与 S3 分别在"变形大"与"序列长"两个
轴的两端最优，S2 居中偏长序列，S4 用复杂度换鲁棒性。

## 4. 现有实现印证（全部在本机磁盘，可复核）

| 实现 | 策略 | 证据 | 备注 |
|---|---|---|---|
| **3D-Stereo-ALDIC**（本项目 MATLAB 版，Exp. Mech. 2025） | S1 | `gui/runPipelineCore.m:74-93`（StereoMatch_STAQ 一次 + TemporalMatch L/R 各一遍） | 我们的对位基线 |
| **ADIC3D**（Atkinson & Becker, SoftwareX） | S1，且时序参考方式已参数化 | `ADIC3D-main/ADIC3D.m:20-25`（`StereoMatch` 一次 + `ImgCorr`×2，`RefStrat` 参数控制 acc/inc） | **可插拔先例**：把参考策略作为参数正是本设计的单相机版 |
| **MultiDIC**（Solav et al., IEEE Access 2018） | S3 | `MultiDIC-1.1.0/main_scripts/STEP2_2DDICusingNcorr.m:1-7`（2n 张图一个 Ncorr 分析，"1st image of the 1st camera is always the reference"） | 借 Ncorr 种子传播消化难匹配；文档自限中等变形 |

三个独立实现覆盖了两种策略端点，且都能产出发表级结果——进一步证明"策略属于
可选项而非对错题"。

---

## 5. 可插拔架构设计

### 5.1 协议与注册表

```python
# al_dic_3d/matching/strategy.py
class CorrespondenceStrategy(Protocol):
    """Turn (sequence, rig, reference mesh) into per-frame image-plane
    positions of the reference material points, in every camera."""
    name: ClassVar[str]
    def compute(
        self,
        seq: StereoSequence,
        rig: StereoRig,                 # epipolar seeding / QC only — never math shortcuts
        mesh_L: DICMesh,                # reference material points (left, frame 1)
        cfg: CorrespondenceConfig,
        progress: Callable[[float, str], None] | None = None,
        stop: Callable[[], bool] | None = None,
    ) -> CorrespondenceSet: ...

STRATEGY_REGISTRY: dict[str, type[CorrespondenceStrategy]] = {
    "track_both": TrackBothStrategy,            # Phase 1
    "stereo_each_frame": StereoEachFrameStrategy,  # Phase 2
    "ref_direct": RefDirectStrategy,            # Phase 2
    # "adaptive": reserved post-v1
}
```

### 5.2 配置与输出契约

```python
@dataclass(frozen=True)
class CorrespondenceConfig:
    strategy: str = "track_both"
    schedule_L: FrameSchedule | None = None   # None → derive from reference_mode
    schedule_R: FrameSchedule | None = None   # track_both only
    stereo_solver: Literal["local_only", "full_aldic"] = "local_only"
    epipolar_seed: bool = True                # bound FFT search along epipolar band
    disparity_offset: tuple[float, float] | None = None  # coarse prior, big baselines
    refresh_interval: int | None = None       # adaptive: periodic re-anchor
    quality: QualityGate = QualityGate()      # znssd_max, reproj_max_px, min_valid_frac

@dataclass(frozen=True)
class CorrespondenceSet:                      # ★ 策略无关、模式无关的隔离墙
    strategy: str
    xL: NDArray       # (n_frames, n_pts, 2), NaN = invalid
    xR: NDArray       # (n_frames, n_pts, 2)
    quality: NDArray  # (n_frames, n_pts)  ZNSSD
    source: NDArray   # (n_frames, n_pts) uint8: 0=TRACKED 1=STEREO_REFRESH 2=RESCUED 3=INVALID
```

设计规则：
- 下游（`reconstruct/strain3d/viz3d/export`）**只允许**消费 `CorrespondenceSet`，
  禁止 import 任何具体策略——用架构测试（import-linter 或等价）固化。
- `source`/`quality` 从 v1 起就填写（S1 全 TRACKED），使 QC 页与 S4 无需 schema 变更。
- 策略实现内部应由**纯函数原语**组装（`stereo_match_pair()`、`temporal_track()`、
  `resample_to_points()`、`compose_increment()`），S4 未来直接复用原语。

### 5.3 原语 `match_points`（3D 侧薄 wrapper，**不改 2D**）

```python
# al_dic_3d/matching/primitives.py  —— 3D 侧实现，import 2D 内部，不修改 2D 仓
def match_points(ref_img, def_img, points: NDArray, U0: NDArray,
                 para: DICPara) -> tuple[NDArray, NDArray, NDArray]:
    """Local IC-GN at arbitrary scattered points (no mesh, no ADMM).
    Returns (U(n,2), znssd(n,), valid(n,)).
    Implemented in al_dic_3d by wrapping al_dic.solver.local_icgn
    (2D's per-node IC-GN loop) — record the import in docs/DEPENDS_ON_2D.md."""
```

> **定位变更（决策 D11）**：早期把它列为"2D v0.7 平台缝 #5"，现降级——2D 仓保持只读锁定，
> 本原语**在 3D 侧实现**：现有 `al_dic.solver.local_icgn` 本就逐节点迭代，此 wrapper 只是把
> "节点坐标来自网格"放宽为"来自调用者"，import 即可、无需动 2D。Phase 1 建立，S2/S3/S4
> 复用。S1（track_both 时序）不依赖它——它走 `run_aldic` 全流程。将来若 wrapper 需触碰过多
> 2D 私有细节，才考虑在单独的 2D 会话里把它提升为 `al_dic.core` 公开 API（见 01 §C.1）。

### 5.4 极线几何的使用边界（决策 D7）

- 匹配在**原始图像**上进行；**不做 rectification**（重采样损伤散斑，且 MATLAB
  参考同样不做）。
- 标定几何仅用于：(a) FFT 搜索带约束/播种（把 2D 搜索压缩到极线带 ±容差，
  大视差场景的加速与防错配）；(b) QC（重投影误差、极线距离残差）。
- 三角化前对**点坐标** undistort（`cv2.undistortPoints` 等价 MATLAB
  `funUndistortPoints`）。

### 5.5 引擎扩展预留（不阻塞 v1）

- **E2：二阶形函数**。跨视角匹配（S2 的大基线角、S3 的大变形）最先受一阶仿射
  形函数限制；MATLAB 侧留有"2nd-order reserved (not implemented)"接口
  （`StereoMatch_STAQ.m:78-81`）。列为 al-dic 引擎的远期扩展，接口上
  `stereo_solver` 已可扩枚举。
- **E3：时域后平滑**。S2 的每帧立体噪声可用位移时间序列的后置平滑消减——
  属后处理模块，不进策略层。

---

## 6. 验证计划（Phase 2 的三策略对比 harness）

1. **数据**：(a) MATLAB baseline 数据集（S1 对位锚）；(b) Stereo-DIC Challenge
   样例；(c) **合成双目真值序列**——用已知 3D 表面 + 位移场经双相机模型渲染散斑
   （注意：变形贴图必须用定点迭代的 Lagrangian warp，沿用 2D 侧的既定做法；
   两视角渲染必须投影一致）。
2. **指标**：位移 RMSE vs 真值；漂移斜率（误差 vs 帧号的线性项）；噪声底
   （去趋势后的 σ）；有效点存活率 vs 帧号；重投影误差 vs 帧号；失败率 vs
   变形幅度（S3 重点）；单帧耗时。
3. **产出**：三策略同数据集对比 PDF（`reports/`），成为用户文档中"何时选哪种
   策略"一节的实证依据。
4. **自洽测试**（与策略正交）：小变形数据上 acc vs inc 结果差 < 噪声底。

## 7. 默认与路线位置

- **v1 默认 `track_both`**：与 MATLAB/已发表结果对位是 MVP 的第一要务，且它最便宜。
- GUI 策略下拉自 Phase 4 起暴露三项 + 说明文案（各策略适用场景，引用 §3 矩阵的
  结论性语言）；`adaptive` 灰显"future"。
- 文档承诺：任何新策略的加入只允许 (a) 新增注册表项，(b) 新增自身参数子面板，
  (c) 复用原语层——不得触碰 `CorrespondenceSet` 之后的任何代码。

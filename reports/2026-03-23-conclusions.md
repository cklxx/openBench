# OpenBench 实验总结论（更新版）

**平台:** OpenBench — Claude Agent A/B 测试平台
**周期:** 2026-03-17 → 2026-03-23（7 天）
**规模:** ~200 个实验组，~6,000 次 trial，~$110 USD
**模型:** claude-haiku-4-5（主力），claude-sonnet-4-6（对照）

---

## 〇、实验方法论

### 平台架构

OpenBench 基于 `claude_agent_sdk`，每个 trial 的执行流程：

```
┌─ 实验定义 (experiments/*.py) ─────────────────────────────────────┐
│  Experiment / TournamentConfig                                    │
│  ├─ agent_a: AgentConfig (model, system_prompt, tools, max_turns) │
│  ├─ agent_b: AgentConfig (只改一个变量 = DiffSpec)                │
│  ├─ tasks: [TaskItem (prompt, check_fn)]                          │
│  ├─ setup_files: {"path": "content"}  ← 预置代码文件              │
│  └─ num_samples: N  ← 每 (agent, task) 跑 N 次                   │
└───────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─ Runner (runner.py) ──────────────────────────────────────────────┐
│  for each (agent, task, sample):                                  │
│    1. tempfile.TemporaryDirectory() ← 隔离工作目录                │
│    2. 写入 setup_files 到临时目录                                 │
│    3. 执行 setup_script (如 git init)                             │
│    4. claude_agent_sdk.query(                                     │
│         prompt = task.prompt,                                     │
│         options = ClaudeAgentOptions(                              │
│           model = agent.model,                                    │
│           system_prompt = agent.system_prompt,                    │
│           allowed_tools = agent.allowed_tools,                    │
│           max_turns = agent.max_turns,                            │
│           cwd = 临时目录                                          │
│         )                                                         │
│       )                                                           │
│    5. 收集: output, tool_call_names, tokens, cost, full_trace     │
│    6. 判定: eval(check_fn, {"output": output}) → correctness     │
│    7. 清理临时目录                                                │
└───────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─ 结果 (results/<name>/*.jsonl) ───────────────────────────────────┐
│  每行一个 TrialResult:                                            │
│  {agent_name, task_index, correctness, output,                    │
│   metrics: {latency_ms, tokens, cost, tool_call_names,            │
│             num_turns, stop_reason},                               │
│   full_trace: [{turn, content, usage}, ...]}                      │
└───────────────────────────────────────────────────────────────────┘
```

### 关键概念

| 概念 | 说明 |
|:--|:--|
| **max_turns** | SDK 的 agentic cycle 数。1 个 turn 可包含多个 tool call + 思考。实际消息数远多于 turn 数 |
| **DiffSpec** | 实验只改 agent_a 和 agent_b 之间的**一个变量**（model、system_prompt、max_turns 等） |
| **check_fn** | Python 表达式，接收 `output` (str)，返回 bool。如 `'"PASSED" in output'` |
| **setup_files** | 每个 trial 的临时目录中预置的代码文件。agent 在这些文件上工作 |
| **隔离** | 每个 trial 有独立的 tempdir，trial 间无共享状态 |
| **full_trace** | 完整的执行轨迹：每个 turn 的 thinking、text、tool_use、tool_result |

### 一个典型实验的具体例子

以 `real_model_selection_v2.py` 为例：

```python
experiment = Experiment(
    name="real_model_selection_v2",
    diff=DiffSpec(field="model", description="Haiku vs Sonnet"),

    agent_a=AgentConfig(
        name="haiku",
        model="claude-haiku-4-5",          # ← 唯一差异
        system_prompt="You are a software developer...",
        allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
        max_turns=15,
    ),
    agent_b=AgentConfig(
        name="sonnet",
        model="claude-sonnet-4-6",          # ← 唯一差异
        system_prompt="You are a software developer...",  # 完全相同
        allowed_tools=["Read", "Write", "Bash", "Glob", "Edit", "Grep"],
        max_turns=15,
    ),

    tasks=[
        TaskItem(
            prompt="Fix the bugs in tasks/t1/urlparse.py. Run: cd tasks/t1 && python test_urlparse.py",
            check_fn='"PASSED" in output or "pass" in output.lower()',
        ),
        # ... T2, T3, T4
    ],

    setup_files={
        "tasks/t1/urlparse.py": '''...有 bug 的代码...''',
        "tasks/t1/test_urlparse.py": '''...测试代码...''',
        # ... 其他任务文件
    },

    num_samples=8,  # 每 (agent, task) 跑 8 次
)
```

执行：`openbench run experiments/real_model_selection_v2.py`

产出：2 agents × 4 tasks × 8 samples = **64 个独立 trial**，每个在隔离的临时目录中执行。

### 数据分析方法

- **correctness**: check_fn 判定（自动化，无人工）
- **per-task breakdown**: 按 task 分组看每个 agent 的正确率
- **stop_reason**: `end_turn`（正常完成）vs `tool_use`（hit max_turns）
- **tool_call_names**: 工具调用序列，用于分析行为模式
- **full_trace**: 完整思考链，用于 root cause 分析

---

## 一、核心发现

### 发现 1：模型能力是阶梯函数（Capability Cliff）

> **任务对模型来说要么 100% 可解，要么 0% 不可解。没有渐进的中间态。**

**实验:** `real_model_selection_v2` — Haiku vs Sonnet，4 个推理难度递增的任务，max_turns=15，n=8

| 任务 | 类型 | Haiku | Sonnet |
|:--|:--|:-:|:-:|
| T1: URL 正则 | 正则表达式修复 | **8/8** | **8/8** |
| T2: 浮点精度 | IEEE 754 陷阱 | **8/8** | **8/8** |
| T3: 闭包捕获 | Python 经典 gotcha | **8/8** | **8/8** |
| T4: 位移编码 | 位运算推理 | **0/8** | **8/8** |

**机制:** T4 要求 agent 手动计算 `65 << 2 = 260, 260 & 0xFF = 4, 4 ^ 0xAA = 0xAE`。Haiku 的权重中不包含可靠的位运算推理能力，无论给多少 turns、什么 prompt，都解不了。Sonnet 可以。

**不是渐进退化：** 不存在"Haiku 50% 能解"的任务。一旦超出能力边界，就是 0%。

---

### 发现 2：Prompt Engineering 几乎无效

> **合理范围内的 prompt 差异对正确率的影响 < 5pp。**

**实验:** `real_prompt_v2` — minimal vs structured prompt，同样的 hard tasks，Haiku，max_turns=15，n=8

| Prompt 风格 | T1 | T2 | T3 | T4 | 总计 |
|:--|:-:|:-:|:-:|:-:|:-:|
| Minimal: "Fix the bugs" | 8/8 | 7/8 | 8/8 | 0/8 | **72%** |
| Structured: "Run→Read→Fix→Review→Verify" | 8/8 | 8/8 | 8/8 | 0/8 | **75%** |

+3pp，在噪声范围内（1 个 trial 的差异）。

**为什么无效：**
- 能力范围内的任务（T1-T3）：agent 不需要 prompt 指导也能解决
- 能力范围外的任务（T4）：再好的 prompt 也帮不了
- 没有"prompt 能帮上忙"的中间地带

---

### 发现 3：Turn-Correctness 曲线是 Sigmoid

> **存在一个 knee 点（~12-14 turns），低于此急降，高于此无效。**

**实验:** `turn_correctness_curve` — tournament，5 个 agent (turns=8/11/14/17/20)，4 个 hard tasks，n=12/agent

| Turns | 正确率 | 平均成本 |
|:-:|:-:|:-:|
| 8 | **72.9%** | $0.039 |
| 11 | **95.8%** | $0.038 |
| 14 | **100%** | $0.039 |
| 17 | **100%** | $0.041 |
| 20 | **100%** | $0.041 |

```
100% ─────────────────────■━━━━━■━━━━━■━━━━━■
 96% ─────────────────■
 73% ───■
     ──┼────┼────┼────┼────┼────→ turns
       8   11   14   17   20
```

**成本几乎恒定**（$0.038-0.041）。agent 无论 budget 多大，自然使用 ~9-10 个 tools。多余的 turns 根本不用。

**实践公式:** `最优 turns = knee × 1.2 ≈ 任务所需最小 tools × 1.5`

---

### 发现 4：便宜模型 + 多 turns 优于贵模型 + 少 turns

> **在模型能力范围内的任务上，Haiku@20 完胜 Sonnet@8。**

**实验:** `model_turns_tradeoff` — Haiku@20turns vs Sonnet@8turns，4 个 hard tasks，n=5

| Agent | 正确率 | 平均成本 |
|:--|:-:|:-:|
| Haiku @ 20 turns | **100%** | **$0.044** |
| Sonnet @ 8 turns | **70%** | $0.081 |

Sonnet@8 失败因为 8 turns 低于 sigmoid knee。Sonnet 并不需要更少的 turns——它需要和 Haiku 同样的 ~14 turns。但 Sonnet 单价更贵。

**最优策略:** 先用 Haiku 试（便宜），失败了再用 Sonnet（能力更强）。

---

### 发现 5：Turn Budget 是此前所有"策略"发现的真正原因

> **给充裕的 turns 后，策略差异消失。此前的"策略发现"本质是 turn 管理效率差异。**

**实验:** `strategy_hints_generous` — discovery vs guided，max_turns=20，4 hard tasks，n=5

| 条件 | discovery | guided | 差异 |
|:--|:-:|:-:|:-:|
| max_turns=8 (紧) | 14/20 | 11/20 | hints 有害 |
| **max_turns=20 (松)** | **20/20** | **20/20** | **差异消失** |

同样，batch vs iterative 在充裕 turns 下也收敛（16/20 vs 15/20，噪声范围）。

**重新解读此前所有发现：**

| 此前结论 | 真正原因 |
|:--|:--|
| Read-first > test-first (+25pp) | Read-first 省 1 turn → 仅在 turn 紧时有效 |
| Batch > incremental (+53pp) | Batch 省 ~50% turns → 仅在 turn 紧时有效 |
| Scratchpad 有害 (-40-100pp) | 笔记消耗 turns → 仅在 turn 紧时有害 |
| Hints 在难任务有害 (-15pp) | Hints 多用 1-2 tools → 仅在 turn 极紧时导致超时 |

---

### 发现 6：早期发现仍然成立（在 turn 紧的场景下）

以上不意味着早期发现是错的。在**实际生产环境中 turn 预算确实有限**（成本、延迟、API 限制），因此：

- **Prompt 合规取决于具体性：** 指定"Start with running the test file"有 100% 合规率，"Start coding"有 0%。
- **最小化修改避免附带损害：** 指示 agent "顺便改善"代码导致 25% 回归。
- **check_fn 有模型偏见：** `"PASSED" in output` 对 Sonnet 不公平（Sonnet 倾向改述而非逐字复制）。

这些不依赖 turn budget，是独立的发现。

---

## 二、Context 管理

### 格式不重要，体积重要

4 种格式（key_value、indexed、json_lines、toon）在准确率上无显著差异（95-100%）。

### Summary + Recent 是最优策略

| 策略 | Prompt 大小 | 准确率 |
|:--|:-:|:-:|
| Full history | 100% | 100% |
| Summary + last 10 | 36% | 74% |
| Last 5 only | 18% | 20% |

### 上下文窗口 = 工作记忆（至少到 30 文件）

**实验:** `context_pressure_boundary` (15 files) + `context_pressure_30files` (30 files)

| 文件数 | Agent 实际读取 | Implicit | Scratchpad | 差距 |
|:-:|:-:|:-:|:-:|:-:|
| 3 | 3 | 100% | 0-65% | 大 |
| 8 | 8 | 100% | 60% | 大 |
| 15 | ~12 | 100% | 20-100%* | 中-大 |
| 30 | **~10** | **100%** | **100%*** | **仅成本差** |

*strict FORBIDDEN 约束: 20%; relaxed "SHOULD" 约束: 100%

**Agent 用测试输出做自然的 fault localization**，30 文件只读 ~10 个。Context 压力取决于需要读的文件数，不是存在的文件数。

---

## 三、实验方法论经验

### 什么制造区分度

| 方法 | 效果 | 例子 |
|:--|:--|:--|
| ❌ 紧 turn budget | 制造人为的"策略"差异 | 8 turns 把 100% 拉到 73% |
| ❌ 人为约束 (FORBIDDEN) | 制造人为失败 | Scratchpad strict: 20% |
| ✅ **模型能力边界的任务** | 真正的区分度 | 位运算: Haiku 0% vs Sonnet 100% |
| ✅ **不同难度的任务组合** | 看清能力分布 | T1-T3 都 100%, T4 分化 |
| ❌ 不同 prompt 措辞 | 几乎无效果 | Minimal vs structured: +3pp |

### 实验设计公式（更新版）

1. **两个 agent 都应该是合理的好配置**——不要人为制造一个差的 agent
2. **任务要跨越模型能力边界**——包含模型能解和不能解的任务
3. **Turn budget 要充裕**——不因超时制造假差异
4. **用 n≥8 获得稳定估计**——n=5 的方差太大（±10pp）
5. **check_fn 要格式无关**——`"pass" in output.lower()`
6. **分析 per-task 而不只看总数**——总数掩盖了阶梯效应

---

## 四、给 Agent 构建者的实践建议

### 模型选择

```
任务在 Haiku 能力范围内？
├── 是 → 用 Haiku（省 60% 成本，正确率相同）
└── 否 → 用 Sonnet（或更强模型）

如何判断？跑 3 次 Haiku。3/3 通过 → Haiku 足够。0/3 → 换 Sonnet。
探测成本：3 × ~$0.10 = $0.30。潜在节省：后续所有 run 省 60%。
```

### Turn Budget

```
最优 turns = sigmoid knee × 1.2
           ≈ 任务所需最少 tools × 1.5

低于 knee：成功率急降，浪费钱
高于 knee：成功率不变，也不多花钱（agent 不会用掉多余的 turns）
```

### System Prompt

**不需要复杂的 prompt engineering。** 一个简洁的 prompt 就够了：

```
You are a software developer. Fix the bugs and make all tests pass.
Print the final test output.
```

结构化 prompt（workflow steps、review 步骤）只增加 ~3pp，不值得维护成本。

**但具体性仍然重要：** 如果需要控制行为（如 tool 选择顺序），用具体动作描述而非模糊策略描述。

### 不要做的事

1. ❌ 不要用 FORBIDDEN/MUST 约束 agent 的工作流——每个约束消耗 turns
2. ❌ 不要给 agent 不确定的 bug 提示——错误提示比不提示更贵（+93% 成本）
3. ❌ 不要强制 agent 写笔记——上下文窗口就是工作记忆
4. ❌ 不要用紧 turn budget 制造压力——压力不是策略差异，只是 timeout
5. ❌ 不要花时间优化 prompt 措辞——把时间花在模型选择和 turn budget 校准上

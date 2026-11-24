# Progressive Knowledge

[English](#english) · [中文](#中文)

A file-based knowledge layer that lets an agent pick a long-running project back up in **~1.5k tokens** instead of re-reading it.

---

## English

### The problem

Every agent session starts with an empty context. Teams work around it in four ways, and all four fail:

1. **Keep the conversation going.** A new session cannot see it, and stuffing history into the window does not work: effective context is far smaller than the advertised size, and long contexts degrade well before their nominal limit.
2. **Write everything into one instructions file.** It becomes a second document set, exceeds what is injected, and starts contradicting itself.
3. **Summarize the history.** Summaries are lossy. Controlled tests retain only a small fraction of recurring details, so the summary silently rewrites the project.
4. **Rely on memory features.** They store *facts* (preferences, corrections). They do not store *project state*: where we are, what is blocked, what was rejected.

The result is the same in every case: the agent asks "where were we?" again, redoes work, or contradicts a decision nobody remembers.

### What this is

A small, auditable file structure built around three artifacts:

| Artifact | Question it answers | Where it lives |
|---|---|---|
| **Entry file** | How do I work here, and where do I look? | `AGENTS.md` (injected every session) |
| **State pointer** | Where are we, what is next, what is blocked? | `docs/STATE.json` |
| **Session logs + decision ledger** | What happened, and what was rejected? | `docs/_sessions/`, `docs/decisions.md` |

Nothing is inferred from conversation history. The entry routes; the state answers "now"; the logs and ledger answer "why" and "what happened".

### How it works

**Three roles, three different reads** — this is the whole trick:

| Role | When | Reads | Cost |
|---|---|---|---|
| Builder | day one, once | the principles quick table + bootstrap + templates | ~3.5k tokens |
| Runner | every session | entry → `STATE.json` → last 3 lines of the session index → **one** document | ~1.5k tokens, capped |
| Auditor | at close | nothing (it scans bytes; never enters the model context) | ~0.7k output |

The entry file contains an **opening protocol** so the runner cannot skip the state: read `STATE.json`, reconcile `last_session` against the newest log, then open exactly one page.

**Tiers** keep small projects light:

| Tier | Principles | Use for |
|---|---|---|
| L0 | 6 | one-off tasks, solo, under a week |
| L1 | 12 | sustained solo work (recommended) |
| L2 | 22 | teams, branches, months |

**Three kinds of writing, three different rules** — the most common source of rot is mixing them:

| Kind | Files | Mode |
|---|---|---|
| State | `STATE.json` | overwrite; it is a projection rebuildable from logs |
| Record | `_sessions/`, `decisions.md` | append only; closing changes a status field and keeps the row |
| Knowledge | `docs/<topic>/*.md` | rewrite in place; delete what is outdated |

### What is in here

```
progressive-knowledge/
├── SKILL.md                 # pi skill entry (loaded on demand)
├── references/              # read on demand, never resident
│   ├── principles.md        # 22 principles, one-line criteria, tiers
│   ├── principles-full.md   # rationale, counter-examples, exceptions
│   ├── bootstrap.md         # 30-minute setup
│   ├── bootstrap-full.md    # no-git fallbacks, migration, scale, failures
│   ├── writing.md           # what to write, how, and what must hold
│   ├── seed.md              # one copy-paste file that makes a model build the layer
│   └── openspec.md          # optional: composition with OpenSpec
├── templates/               # entry, state, decisions, session, index (+ OpenSpec variants)
├── scripts/
│   ├── check.py             # zero-dependency minimal checker
│   ├── audit.py             # 22 principles, tiers, configurable
│   └── audit.config.json    # thresholds, paths, vocabulary
├── example/                 # complete workspace that passes L2 with 0 FAIL / 0 WARN
└── .github/workflows/check.yml
```

### Quick start

**As a pi skill**

```bash
git clone https://github.com/twn1993/progressive-knowledge ~/.pi/agent/skills/progressive-knowledge
# then, in pi: /reload
/skill:progressive-knowledge
```

The skill inspects the project, writes `AGENTS.md`, creates `docs/`, installs `tools/check.py`, and runs it until clean.

**By hand**

```bash
mkdir -p <ws>/docs/_sessions <ws>/tools
cp scripts/check.py <ws>/tools/
cp templates/AGENTS.md.tmpl <ws>/AGENTS.md       # fill placeholders
cp templates/STATE.json.tmpl <ws>/docs/STATE.json
python <ws>/tools/check.py <ws>                  # must be FAIL 0
```

**Verify this repository**

```bash
python scripts/audit.py example --tier L2   # 22/22 PASS, 0 FAIL, 0 WARN
python scripts/check.py example             # FAIL 0, WARN 0
```

### The 22 principles (quick table)

| ID | Principle | Tier |
|---|---|---|
| P01 | One entry file with a size cap | L0 |
| P02 | Intent routing, no linear reading | L1 |
| P03 | Sub-domain files implement, never relax | L2 |
| P04 | Zero volatile facts in the resident layer | L0 |
| P05 | Per-page maximum **and minimum** | L1 |
| P06 | Contents, tables, section size | L2 |
| P07 | No dangling links or anchors | L1 |
| P08 | Fixed confidence vocabulary | L2 |
| P09 | Living docs carry no history; archive is not an entry | L2 |
| P10 | One authority per fact | L2 |
| P11 | A single-source claim must have no copies | L2 |
| P12 | Decision ledger: four fields, closed status set | L2 |
| P13 | Open items are consumable (and closable) | L1 |
| P14 | Exactly one machine-readable state pointer | L0 |
| P15 | Only re-derive commands; reconcile on open | L0 |
| P16 | Append-only session logs | L0 |
| P17 | Write-back names file, section, and trigger | L1 |
| P18 | A check entry point in the workspace | L0 |
| P19 | Irreversible operations, with failure modes | L2 |
| P20 | Conclusion wording discipline | L2 |
| P21 | Cold-start budget, single routing table | L2 |
| P22 | Evidence resolves (`path:line` exists) | L1 |

Full detail: [`references/principles-full.md`](references/principles-full.md).

### Two checkers

| | `scripts/check.py` | `scripts/audit.py` |
|---|---|---|
| Dependencies | none | none |
| Scope | entry, sizes (max/min), contents, links, anchors, `path:line`, volatile values, state fields, session logs, duplicate routing, duplicated long sentences | all 22 principles, tiers, config file, manual-check list, JSON output |
| Use | smallest possible gate; safe to vendor into a workspace | full audit and CI |

Both are read-only and never modify a workspace.

### Example

`example/` is a working workspace (a research-style project) with:

- a 71-line entry containing the opening protocol;
- `STATE.json` with two open items, one of them `done`;
- a decision ledger with adopted / rejected / failed rows;
- append-only session logs;
- evidence cards citing `_sources/A/spec.md:3` and `_sources/B/summary.csv:1`.

It passes L0, L1, and L2 with no findings. `ci/check.yml` is the same check as a GitHub Actions workflow — copy it to `.github/workflows/` once your token has the `workflow` scope.

### Why this shape (design notes)

- **Effective context is much smaller than advertised**, and retrieval beats stuffing. So the entry is a router, not a container.
- **LLM summaries lose detail.** So evidence is kept as original text plus `path:line`, and summaries are used only as indexes.
- **Status written into prose expires.** A project that wrote status into its entry had six stale claims within seven days. So status is one JSON file with re-derive commands.
- **Copies diverge.** The same rule copied into three places was different in all three. So one authority per fact, everything else links.
- **"Remember to update" never happens.** So a check command plus a closing checklist, enforced by CI or a hook.

### Verified

| Target | Result |
|---|---|
| `example/` | L0 6/6, L1 12/12, L2 22/22 — 0 FAIL, 0 WARN |
| Negative control (inject `HEAD a1b2c3d`, break links) | fails as expected |
| A real long-running project | 6 FAIL at L1: stale status claims, an oversized page, missing state/session/check layers |
| Cross-session bootstrap | a generated layer resumed with a ~1.5k-token cold start |

### Honest limits

1. There is **no controlled experiment** showing files beat vector stores. What is supported is "retrieval beats stuffing" and "summaries lose detail". Files are the cheapest retrievable backend, not a proven optimum.
2. `P10`, `P11`, `P13` are heuristics. 3-gram similarity misses paraphrased duplicates and flags template repetition.
3. Line limits are a proxy, not proof that a session fits.
4. It depends on someone writing twenty lines at the end of a session. Without `P18` (a check entry point), the rest rots within weeks.
5. The entry cannot guarantee truth. In a real generation test, the mechanically clean layer still contained three factual errors; that is why P20 and P22 exist.

### Composing with OpenSpec

OpenSpec owns changes and specs; this layer owns project state, session memory, and evidence. `templates/AGENTS.openspec.md.tmpl` and `references/openspec.md` describe the split, the initialization order, and the three checks worth adding.

### License

MIT.

---

## 中文

### 问题

每个 agent session 都从空上下文开始。常见四种绕法，全部失败：

1. **一直开着同一个会话。** 新会话看不到；把历史塞进窗口也不行——有效上下文远小于标称值，长上下文在到达名义上限之前就开始退化。
2. **把所有东西写进一个指令文件。** 它会变成第二套文档，超出注入预算，然后开始自相矛盾。
3. **把历史摘成摘要。** 摘要有损：受控实验里"反复出现的细节"只保留很小一部分，等于让摘要悄悄改写项目。
4. **依赖记忆功能。** 它们存的是**事实**（偏好、纠正），不是**项目状态**（现在在哪、卡在哪、否决过什么）。

结果总是一样：agent 再问一遍"我们做到哪了"，重做已经做过的事，或者推翻一个没人记得的决策。

### 这是什么

一套小到可以审阅的文件结构，围绕三件东西：

| 东西 | 回答什么 | 在哪 |
|---|---|---|
| **入口文件** | 我在这里怎么干活、该看哪里 | `AGENTS.md`（每次 session 自动注入） |
| **状态指针** | 现在在哪、下一步、卡在哪 | `docs/STATE.json` |
| **会话日志 + 决策账** | 发生了什么、否决过什么 | `docs/_sessions/`、`docs/decisions.md` |

不从对话历史里推断任何东西：入口负责路由，状态回答"现在"，日志与决策账回答"为什么"和"发生过什么"。

### 怎么运作

**三种角色，三种读法**——这是全部的诀窍：

| 角色 | 何时 | 读什么 | 成本 |
|---|---|---|---|
| 建库者 | 第一天，一次 | 原则速查 + 落地指南 + 模板 | 约 3.5k tokens |
| 运行者 | 每个 session | 入口 → `STATE.json` → 会话索引末 3 行 → **一篇**正文 | 约 1.5k tokens，有上限 |
| 审计者 | 收尾 | 不读（机械扫描字节，不进模型上下文） | 输出约 0.7k |

入口文件里有**开场协议**，运行者无法跳过状态：先读 `STATE.json`，比对 `last_session` 与最新会话文件，然后只打开一页。

**档位**让小项目保持轻量：

| 档 | 断言 | 适合 |
|---|---|---|
| L0 | 6 | 一次性任务、单人、一周内 |
| L1 | 12 | 单人持续推进（推荐） |
| L2 | 22 | 多人、多分支、数月 |

**三种写入，三套规则**——文档腐烂最常见的原因就是把它们混在一起：

| 类型 | 文件 | 方式 |
|---|---|---|
| 状态 | `STATE.json` | 覆盖；它是投影，可从日志重建 |
| 记录 | `_sessions/`、`decisions.md` | 只追加；关闭只改状态字段并保留一行 |
| 知识 | `docs/<主题>/*.md` | 就地改写；过时即删 |

### 仓库结构

```
progressive-knowledge/
├── SKILL.md                 # pi skill 入口（触发时才加载）
├── references/              # 按需读，从不常驻
│   ├── principles.md        # 22 条断言速查 + 档位
│   ├── principles-full.md   # 理由、反例、例外
│   ├── bootstrap.md         # 30 分钟落地
│   ├── bootstrap-full.md    # 无 git 代偿、迁移、规模、失败模式
│   ├── writing.md           # 写什么、怎么写、写完要满足什么
│   ├── seed.md              # 单文件引导：让模型自己建这一层
│   └── openspec.md          # 可选：与 OpenSpec 拼装
├── templates/               # 入口、状态、决策、会话、索引（含 OpenSpec 两版）
├── scripts/
│   ├── check.py             # 零依赖最小自检
│   ├── audit.py             # 22 条断言、分档、可配置
│   └── audit.config.json    # 阈值、路径、词表
├── example/                 # 完整示例工作区（L2 全 PASS）
└── .github/workflows/check.yml
```

### 快速开始

**作为 pi skill**

```bash
git clone https://github.com/twn1993/progressive-knowledge ~/.pi/agent/skills/progressive-knowledge
# 然后在 pi 里执行 /reload
/skill:progressive-knowledge
```

技能会检查项目、写 `AGENTS.md`、建 `docs/`、装 `tools/check.py`，并跑到没有 FAIL。

**手动建**

```bash
mkdir -p <ws>/docs/_sessions <ws>/tools
cp scripts/check.py <ws>/tools/
cp templates/AGENTS.md.tmpl <ws>/AGENTS.md       # 填占位符
cp templates/STATE.json.tmpl <ws>/docs/STATE.json
python <ws>/tools/check.py <ws>                  # 必须 FAIL 0
```

**验证本仓库**

```bash
python scripts/audit.py example --tier L2   # 22/22 PASS，0 FAIL，0 WARN
python scripts/check.py example             # FAIL 0，WARN 0
```

### 22 条断言（速查）

| ID | 断言 | 档 |
|---|---|---|
| P01 | 唯一入口 + 体量上限 | L0 |
| P02 | 意图路由，禁止顺序通读 | L1 |
| P03 | 子域只落地、不放松 | L2 |
| P04 | 常驻层零易变事实 | L0 |
| P05 | 单篇上限**与下限** | L1 |
| P06 | 目录、表格、节长 | L2 |
| P07 | 链接与锚点零悬空 | L1 |
| P08 | 证据分级词表固定 | L2 |
| P09 | 活文档不存历史；归档不作入口 | L2 |
| P10 | 一个事实一处权威 | L2 |
| P11 | 「唯一权威」声明必须无副本 | L2 |
| P12 | 决策账四字段 + 状态闭集 | L2 |
| P13 | 待办可消费（且可关闭） | L1 |
| P14 | 状态恰一份机器可读指针 | L0 |
| P15 | 只写重取方法；开场对账 | L0 |
| P16 | append-only 会话日志 | L0 |
| P17 | 回写义务指名文件、章节、触发器 | L1 |
| P18 | 仓内必须有 check 入口 | L0 |
| P19 | 不可逆操作清单 + 事故形态 | L2 |
| P20 | 结论措辞纪律 | L2 |
| P21 | 冷启动预算 + 单一路由表 | L2 |
| P22 | 证据可解析（`path:line` 真实存在） | L1 |

详述见 [`references/principles-full.md`](references/principles-full.md)。

### 两个检查器

| | `scripts/check.py` | `scripts/audit.py` |
|---|---|---|
| 依赖 | 无 | 无 |
| 范围 | 入口、行数上下限、目录、链接、锚点、`path:line`、易变值、状态字段、会话日志、双路由、重复长句 | 22 条断言、分档、配置文件、人工清单、JSON 输出 |
| 用途 | 最小门槛，可直接 vendored 进工作区 | 完整审计与 CI |

两者都只读，不会修改工作区。

### 示例

`example/` 是一个可运行的研究型工作区：

- 71 行入口，含开场协议；
- `STATE.json` 两条待办（其中一条 `done`）；
- 决策账含 adopted / rejected / failed 三类；
- 只追加的会话日志；
- 证据卡引用 `_sources/A/spec.md:3` 与 `_sources/B/summary.csv:1`。

它在 L0/L1/L2 下均无任何发现。`ci/check.yml` 是同一套检查的 GitHub Actions 版本——token 具备 `workflow` scope 后复制到 `.github/workflows/` 即可启用。

### 为什么是这个形状（设计说明）

- **有效上下文远小于标称值**，检索优于塞入。所以入口是路由器，不是容器。
- **LLM 摘要会丢细节**。所以证据保留原文 + `path:line`，摘要只做索引。
- **写进散文里的状态一定会过期**：一个把状态写进入口的项目，七天内出现 6 处过期断言。所以状态只有一份 JSON，且只写重取命令。
- **副本必然分叉**：同一条规则抄在三处，三处都不一样。所以一处权威，其余只链接。
- **"记得更新"从来不会发生**。所以一条 check 命令 + 收尾清单，由 CI 或 hook 执行。

### 已验证

| 对象 | 结果 |
|---|---|
| `example/` | L0 6/6、L1 12/12、L2 22/22，0 FAIL / 0 WARN |
| 负向控制（注入 `HEAD a1b2c3d`、制造断链） | 按预期 FAIL |
| 一个真实长期项目 | L1 下 6 FAIL：过期状态、超长页、缺状态/会话/检查层 |
| 跨 session 冷启动 | 生成的层以约 1.5k tokens 接上 |

### 诚实的边界

1. **"文件化优于向量库"没有受控实验**。被支持的是"检索优于塞入"与"摘要会丢细节"；文件只是最便宜的可检索后端。
2. `P10`、`P11`、`P13` 是启发式：3-gram 会漏掉改写过的重复，也会把模板化重复报成警告。
3. 行数上限是代理指标，不能证明"一个 session 装得下"。
4. 它依赖有人在收尾写 20 行。没有 `P18`（check 入口），其余各条几周内就会腐坏。
5. 入口不能保证内容为真。一次真实生成测试里，机械上全干净的层仍含 3 处事实错误——这正是 P20 与 P22 存在的理由。

### 与 OpenSpec 拼装

OpenSpec 管变更与规格；这一层管项目状态、会话记忆与证据。`templates/AGENTS.openspec.md.tmpl` 与 `references/openspec.md` 说明分工、初始化顺序与三条值得加的检查。

### 许可

MIT。

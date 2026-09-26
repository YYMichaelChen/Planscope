# Scoped Planning with Files

> A lightweight, scoped, file-based planning system for long-running software projects.

**Version:** Draft v1.0
**Status:** Implementation Ready
**Working Name:** `planscope`（原 working name `scoped-planning-with-files`，已定为正式 Skill 名）

# 1. 项目简介

`Scoped Planning with Files` 是一个面向 AI Coding Agent 的轻量级长期项目规划 Skill。

它建立在“使用项目文件作为持久化工作记忆”的思想之上，但重点解决传统 file-based planning 在长期开发过程中经常出现的四类问题：

1. Planning 文档随着开发持续增长，最终变得臃肿且难以维护。
2. 很多局部修改不需要完整项目上下文，但 Agent 仍然读取大量 planning 文件，浪费 Context Window。
3. 长期 Roadmap、当前 Release、当前任务、过期 Progress 和历史 Findings 混杂在一起。
4. Planning 文件名称、章节和内容格式容易随着 Agent 和 Session 改变而逐渐失控。

本项目的核心思想不是：

> 把更多上下文保存到文件。

而是：

> **把项目上下文分层保存，并始终只加载当前任务真正需要的 Working Set。**

核心模型：

```
Persistent Knowledge
        ↓
Scoped Storage
        ↓
Context Routing
        ↓
Small Working Set
        ↓
Agent
```

# 2. 设计目标

本 Skill 主要解决长期软件项目中 AI Agent 的 Context Management 问题。

设计目标包括：

### 2.1 Context 最小化

Agent 不应该因为存在 Planning 系统，就默认读取所有 Planning 文件。

任何一次工作开始时，都应该先判断：

```
这次任务实际需要多少项目上下文？
```

然后只读取必要部分。

### 2.2 生命周期隔离

不同生命周期的信息必须分别保存：

```
长期项目知识
当前 Release
当前工作状态
历史 Release
```

长期信息不能和短期 Progress 混在一起。

### 2.3 Planning 文件有明确边界

每一种 Planning 文件只能承担一个明确职责。

不允许出现：

```
dev_notes.md
plan-v2-final.md
new_findings.md
latest_progress.md
implementation-plan.md
todo-next.md
```

等任意扩张的 Planning 文件。

### 2.4 历史信息自动退出 Working Set

Release 完成以后，其：

```
PLAN
KNOWLEDGE
LOG
```

必须退出 active context。

历史资料仍然保留，但默认不得加载。

### 2.5 小任务不承担 Planning Tax

修改一个 CSS、rename、typo、简单 bug fix 等工作，不应该因为安装了 Skill 而自动产生大量 Planning 操作。

Planning 是工具，而不是仪式。

### 2.6 Markdown First

第一版保持：

```
Markdown
+
简单脚本
```

不引入：

```
数据库
复杂状态机
向量数据库
Agent Runtime
DAG Scheduler
```

只有在后续确实需要多 Agent、并发或者机器级状态一致性时，再进行升级。

# 3. 非目标

v1.0 明确不解决以下问题：

- 多 Agent 分布式任务调度
- Worker Lease
- Agent 并发锁
- DAG 自动任务调度
- 基于数据库的 Event Sourcing
- 自动执行项目命令
- Transcript 自动读取
- Autonomous Agent 无限循环
- 自动推断所有项目知识
- 替代 Git
- 替代 Issue Tracker
- 替代完整项目文档系统

这个 Skill 的职责只有一个：

> **让 AI 在长期项目中以更小、更准确、更及时的 Context Working Set 工作。**

# 4. 核心架构

整个系统分为四层。

```
┌─────────────────────────────┐
│         PROJECT             │
│   长期稳定项目上下文         │
├─────────────────────────────┤
│         ROADMAP             │
│   长期方向，不包含实现细节    │
├─────────────────────────────┤
│         RELEASE             │
│   当前版本计划和有效知识      │
├─────────────────────────────┤
│         WORKING             │
│   当前任务和最近执行状态      │
└─────────────────────────────┘
```

Agent 不应该从最上层一路全部读取。

正确顺序是：

```
Current Task
     ↓
INDEX
     ↓
Determine Scope
     ↓
Load Relevant Layer Only
```

# 5. 标准目录结构

所有 Planning 文件统一放在：

```
.planning/
```

标准结构：

```
.planning/
│
├── INDEX.md
├── PROJECT.md
├── ROADMAP.md
│
├── releases/
│   └── v0.8/
│       ├── PLAN.md
│       ├── KNOWLEDGE.md
│       ├── LOG.md
│       └── SUMMARY.md
│
└── archive/
    ├── v0.6/
    │   ├── PLAN.md
    │   ├── KNOWLEDGE.md
    │   ├── LOG.md
    │   └── SUMMARY.md
    │
    └── v0.7/
```

其中：

```
INDEX.md
PROJECT.md
ROADMAP.md
```

为项目级文件。

每一个 Active Release 只允许包含：

```
PLAN.md
KNOWLEDGE.md
LOG.md
SUMMARY.md
```

禁止 Agent 自行创建新的 Planning 文件类型。

# 6. 文件职责

## 6.1 INDEX.md

`INDEX.md` 是整个 Planning 系统的入口。

它应该：

- 非常短；
- 始终保持最新；
- 告诉 Agent 当前工作在哪里；
- 告诉 Agent进一步 Context 在哪里；
- 不保存大量历史信息。

**INDEX 是默认唯一需要读取的 Planning 文件。**

推荐容量：

```
< 80 lines
< 1500 tokens
```

标准结构：

```
# Planning Index

## Active Release

v0.8

Path:
releases/v0.8/

## Current Focus

T-014 Refresh-token expiration fix

## Current Phase

P2 Implementation

## Next Action

Fix expiration calculation in `src/auth/token.ts`.

## Current Blockers

None.

## Context Map

Project context:
PROJECT.md

Roadmap:
ROADMAP.md

Current release plan:
releases/v0.8/PLAN.md

Current release knowledge:
releases/v0.8/KNOWLEDGE.md

Recent activity:
releases/v0.8/LOG.md

## Critical Constraints

- Public API must remain backward compatible.
- Database migrations must be reversible.
```

# 7. PROJECT.md

`PROJECT.md` 保存跨 Release 稳定的信息。

允许存储：

```
Architecture
Technical Constraints
Project Conventions
Stable Domain Knowledge
Long-Term Decisions
```

禁止存储：

```
当前任务
昨天做了什么
Release 临时 Bug
临时调试信息
未来版本详细计划
测试执行记录
```

推荐结构：

```
# Project Context

## Architecture

### Frontend

Next.js

### Backend

FastAPI

### Database

PostgreSQL

## Core Constraints

- Public APIs must remain backward compatible.
- Database migrations must be reversible.
- Credentials must never be stored in plaintext.

## Development Conventions

- Backend features require tests.
- Shared frontend components live under `components/common`.

## Stable Domain Knowledge

...

## Long-Term Decisions

### D-001

Decision:
Use PostgreSQL as the primary transactional database.

Reason:
...
```

PROJECT 默认不读取。

只有以下工作需要读取：

```
Architecture
Cross-module change
Technical decision
Core constraint related change
Long-term design
```

# 8. ROADMAP.md

ROADMAP 只描述长期方向。

定义：

> ROADMAP 表示 Intent，而 PLAN 表示 Commitment。

ROADMAP 示例：

```
# Product Roadmap

## v0.8

Authentication reliability.

## v0.9

Permission model.

## v1.0

Public API stabilization.

## Later

Plugin ecosystem.
```

ROADMAP 禁止出现：

```
implementation checklist
debug notes
详细技术方案
test results
当前任务
```

未来 Release 在真正开始之前不得创建详细 PLAN。

例如：

```
ROADMAP v0.9
```

只是方向。

直到：

```
v0.9 becomes active
```

才创建：

```
releases/v0.9/PLAN.md
```

# 9. PLAN.md

PLAN 只负责：

> 当前 Active Release 尚未完成的计划。

PLAN 必须始终保持“未来导向”。

标准 Schema：

```
# Release v0.8

## Objective

Improve authentication reliability without breaking the public API.

## Acceptance Criteria

- Existing authentication APIs remain compatible.
- Refresh token rotation works correctly.
- Authentication test suite passes.

## Status

in_progress

## Current

Phase: P2
Task: T-014

## Phases

### P1 Architecture

Status: complete

Summary:

Token validation architecture finalized.

Related:
D-003
F-005

### P2 Refresh Token

Status: in_progress

Tasks:

- [ ] T-014 Fix expiration calculation
- [ ] T-015 Implement token rotation tests

### P3 Session Management

Status: pending

Tasks:

- [ ] T-016 Review session invalidation
- [ ] T-017 Add integration tests

## Blockers

None.

## Next Action

T-014 Fix expiration calculation.
```

# 10. Phase 命名协议

Phase ID 必须统一：

```
P1
P2
P3
...
```

Task ID：

```
T-001
T-002
T-003
...
```

Finding ID：

```
F-001
F-002
...
```

Decision ID：

```
D-001
D-002
...
```

禁止创建：

```
phase-final
phase-auth-v2
implementation-last-step
new-task-auth
```

ID 是稳定标识。

自然语言只作为描述。

例如：

```
P2 — Refresh Token
T-014 — Fix expiration calculation
F-009 — Redis TTL uses seconds
D-004 — Keep token validation synchronous
```

# 11. Completed Phase 压缩规则

完成的 Phase 不应该永远保存完整 checklist。

例如：

```
### P1 Investigation

- [x] Search existing implementation
- [x] Review token parser
- [x] Compare JWT library
- [x] Run tests
- [x] Fix parser
- [x] Retest
```

Phase 完成以后应压缩为：

```
### P1 Investigation

Status: complete

Summary:

Existing token validation architecture was reviewed and retained.

Related:
D-003
F-005
```

详细过程由：

```
Git history
LOG
Archive
```

负责保存。

PLAN 的主要内容永远应该是：

> 还没有完成什么。

# 12. KNOWLEDGE.md

KNOWLEDGE 替代传统 `findings.md`。

区别非常重要。

传统 Findings 的逻辑是：

> 发现了什么就写什么。

KNOWLEDGE 的逻辑是：

> **只有未来工作仍然可能需要知道的信息才保存。**

判断标准：

```
如果 Context 现在完全丢失，
未来 Agent 不知道这件事情，
是否可能因此做错事？
```

如果答案是否定的：

> 不写 KNOWLEDGE。

# 13. KNOWLEDGE 标准格式

```
# Release Knowledge

## F-001

Title:
Refresh-token TTL unit

Scope:
release

Related:
T-014

Finding:

Refresh-token TTL is stored in seconds.

Source:

`src/auth/config.ts`

Impact:

Expiration calculations must not treat the value as milliseconds.
```

允许 Scope：

```
task
release
project
```

含义：

### task

仅当前 Task 有价值。

Task 完成以后可以删除。

### release

当前 Release 有价值。

Release Close 后进入 archive。

### project

长期有效。

Release Close 时应该 Promote 到 PROJECT。

# 14. 什么不应该进入 KNOWLEDGE

以下信息不应该记录：

```
打开了哪个文件
运行了一次 grep
一次成功的普通命令
随时重新读取源码就能知道的信息
没有未来决策价值的搜索结果
Agent 自己的思考过程
普通 Git diff 信息
```

例如：

```
package.json currently contains axios 1.7.2
```

通常没有必要。

因为：

```
读取 package.json
```

即可恢复。

但：

```
Do not upgrade axios because the internal plugin depends on legacy interceptor ordering.
```

值得保存。

因为源码本身不一定能直接表达这个约束。

# 15. LOG.md

LOG 是：

> Rolling Working Log。

LOG 不是永久历史。

它只保存：

```
当前工作状态
最近重要执行
最近验证结果
当前 Blocker
尚未被 Promote 的临时上下文
```

推荐最大：

```
100–150 lines
```

示例：

```
# Work Log

## Current State

Phase:
P2

Task:
T-014

Next:
Fix refresh-token expiration calculation.

Blockers:
None.

## Recent Activity

### 2026-09-26

Completed:
T-013

Changed:
Authentication parser refactor completed.

Validation:

`pytest tests/auth`

Result:
Pass.

Promoted:

F-008

### 2026-09-25

Investigated token TTL mismatch.

Promoted:

F-007
```

# 16. LOG 不替代 Git

不要重复记录 Git 已经明确保存的信息。

例如没必要：

```
Modified:
src/a.ts
src/b.ts
src/c.ts
```

如果：

```
git diff
```

就可以获取。

LOG 应该优先保存 Git 不容易表达的信息：

```
为什么这样改
当前验证状态
尚未解决的问题
临时实验结论
下一步准备做什么
```

# 17. SUMMARY.md

SUMMARY 默认在 Active Release 中可以不存在。

Release 完成时生成。

标准格式：

```
# Release v0.8 Summary

## Objective

Improve authentication reliability.

## Delivered

- Refresh-token rotation.
- Session invalidation improvements.
- Authentication test coverage.

## Important Decisions

- D-003 ...
- D-007 ...

## Promoted Project Knowledge

- Refresh token rotation is mandatory.
- Authentication API remains backward compatible.

## Known Limitations

...

## Follow-Up Candidates

...
```

SUMMARY 是：

> Release 历史的高密度索引。

以后需要了解旧版本时：

```
先读 SUMMARY
```

而不是：

```
PLAN
KNOWLEDGE
LOG
全部读取
```

# 18. Context Routing Protocol

这是整个 Skill 最重要的运行规则。

Agent 开始工作时：

```
User Request
      ↓
Classify Scope
      ↓
Need Planning Context?
      ↓
Read INDEX
      ↓
Load only required files
```

不得默认执行：

```
read PROJECT
read ROADMAP
read PLAN
read KNOWLEDGE
read LOG
```

# 19. Task Classification

所有任务大致分成四类。

| Class               | 示例                               | Context                                        |
| ------------------- | ---------------------------------- | ---------------------------------------------- |
| Micro               | typo、rename、CSS、小配置修改      | None / INDEX                                   |
| Local               | 明确 Bug、单模块修改               | INDEX + relevant PLAN                          |
| Feature             | 当前 Release Feature               | INDEX + PLAN + relevant KNOWLEDGE              |
| Planning / Recovery | 版本设计、大范围重构、Session 恢复 | INDEX + PLAN + relevant KNOWLEDGE + recent LOG |

PROJECT 只有在：

```
architecture
cross-module constraints
long-term decisions
project convention
```

相关时才加载。

ROADMAP 只有在：

```
future planning
release sequencing
scope discussion
```

相关时加载。

Archive 默认永远不加载。

# 20. Micro Change Rule

满足以下条件时，应跳过 Planning Workflow：

```
目标明确
影响范围局部
预计修改 <= 2 个文件
不涉及 Architecture
不涉及 Release Scope
不产生长期 Decision
不需要复杂 Research
```

例如：

```
Fix README typo.

Change button padding.

Rename local variable.

Adjust CSS hover state.
```

允许：

```
不读 Planning
不更新 PLAN
不写 LOG
不产生 KNOWLEDGE
```

如果任务涉及实际代码行为，但仍然很小：

```
只读取 INDEX
```

即可。

# 21. Archive Rule

Agent 默认禁止读取：

```
.planning/archive/
```

除非满足：

```
用户明确要求查看历史版本
当前 Bug 明确属于 Regression Investigation
当前问题引用旧 Release
Active Summary 指向历史资料
```

历史信息搜索顺序：

```
SUMMARY
↓
Search archive
↓
Read relevant section
```

不得：

```
直接读取整个历史 Release
```

# 22. Release 生命周期

标准生命周期：

```
ROADMAP
   ↓
OPEN RELEASE
   ↓
ACTIVE DEVELOPMENT
   ↓
COMPACT
   ↓
VERIFY
   ↓
CLOSE RELEASE
   ↓
PROMOTE
   ↓
ARCHIVE
```

# 23. Open Release

开始新版本时：

创建：

```
releases/<version>/
```

包含：

```
PLAN.md
KNOWLEDGE.md
LOG.md
```

更新：

```
INDEX.md
```

ROADMAP 对应 Release 保留简短描述即可。

# 24. Active Development

开发过程中遵循：

```
PLAN → 尚未完成的工作
KNOWLEDGE → 以后仍需知道的信息
LOG → 最近执行上下文
INDEX → 当前工作指针
```

每完成重要 Task：

更新：

```
PLAN
INDEX
```

只有存在实际执行上下文需要恢复时：

更新：

```
LOG
```

只有发现未来工作可能重新需要的信息时：

更新：

```
KNOWLEDGE
```

# 25. Compact

Compact 是文档垃圾回收机制。

以下情况应触发：

```
PLAN > 250 lines
KNOWLEDGE > 200 lines
LOG > 150 lines
一个 Phase 完成
一个大型 Task 完成
Context 明显出现重复
```

Compact 操作包括：

### PLAN

```
Completed checklist
→ Summary
```

### KNOWLEDGE

```
Duplicate findings
→ Merge

Resolved task-scoped finding
→ Drop

Stable project finding
→ Mark for promotion
```

### LOG

```
Old activity
→ Drop / Archive

Relevant conclusion
→ KNOWLEDGE
```

### INDEX

重新生成：

```
Current Focus
Current Phase
Next Action
Blockers
```

# 26. Release Close

Release Close 必须执行以下流程：

```
Verify completion

↓

Generate SUMMARY

↓

Review KNOWLEDGE

↓

Promote project-scope knowledge

↓

Archive remaining release context

↓

Update ROADMAP

↓

Update INDEX

↓

Activate next release or clear active release
```

# 27. Promote Rule

Release Close 时：

```
Scope: project
```

的信息：

```
KNOWLEDGE
    ↓
PROJECT
```

但必须进行：

```
deduplicate
summarize
merge
```

禁止简单复制。

例如：

Release Finding：

```
F-018

Refresh tokens are rotated after every successful refresh.
```

如果已经成为稳定系统行为：

Promote 到：

```
## Authentication Constraints

Refresh tokens are single-use and rotated after every successful refresh.
```

然后旧 Finding 留在 archive。

# 28. Recover Protocol

Session 中断或者 Context 被清理后，不应该读取所有 Planning 文档。

标准恢复：

```
1. Read INDEX

2. Read current PLAN

3. Inspect git diff/status when relevant

4. Search relevant KNOWLEDGE

5. Read latest LOG section only if execution continuity is needed

6. Continue from Next Action
```

只有必要时才读取 PROJECT。

不得默认读取：

```
ROADMAP
Archive
完整 LOG
完整历史 Release
```

# 29. 文档预算

推荐默认：

| File      | Soft Limit | Hard Review |
| --------- | ---------- | ----------- |
| INDEX     | 80 lines   | 120         |
| PROJECT   | 250        | 400         |
| ROADMAP   | 150        | 250         |
| PLAN      | 200        | 300         |
| KNOWLEDGE | 200        | 300         |
| LOG       | 120        | 180         |
| SUMMARY   | 100        | 150         |

超过 Soft Limit：

```
建议 Compact
```

超过 Hard Review：

```
必须 Compact 后再继续扩张
```

这些限制不是硬编码格式要求，而是 Context Hygiene Guardrail。

# 30. Planning 文件创建规则

Agent 不允许主动创建新的 Planning 文档类型。

合法文件只有：

```
INDEX.md
PROJECT.md
ROADMAP.md
PLAN.md
KNOWLEDGE.md
LOG.md
SUMMARY.md
```

如果 Agent 想创建：

```
api_notes.md
investigation.md
implementation_notes.md
```

首先必须判断内容属于：

```
PLAN
KNOWLEDGE
LOG
PROJECT
```

如果都不属于：

优先：

```
不要创建 Planning 文件。
```

技术文档属于产品本身时，应进入项目正式文档目录，例如：

```
docs/
```

而不是 `.planning/`。

# 31. Helper CLI

提供一个轻量 helper：

```
plan.py
```

通过以下方式调用（兼容 Windows 与 Unix，纯 Python 3 标准库）：

```
python <SKILL.md 所在目录>/scripts/plan.py <command>
```

v1 不需要复杂 Runtime。

建议提供以下命令：

```
plan status

plan init

plan open v0.8

plan compact

plan close v0.8

plan doctor
```

# 32. `plan status`

输出：

```
Active release: v0.8
Current phase: P2
Current task: T-014

INDEX        47 lines   OK
PLAN        132 lines   OK
KNOWLEDGE    89 lines   OK
LOG         141 lines   COMPACT RECOMMENDED

Next:
T-014 Fix refresh-token expiration calculation
```

# 33. `plan compact`

职责：

```
检测文档大小
提醒 Agent 进行压缩
可自动 rotate LOG
校验 INDEX 指针
检测非法 Planning 文件
```

第一版不要自动删除 KNOWLEDGE。

涉及语义判断的内容交给 Agent。

机械操作由脚本执行。

# 34. `plan close`

职责：

```
检查当前 PLAN 是否存在 pending/in_progress phase
确认 SUMMARY 已生成
移动 Release 到 archive
更新 INDEX
```

不自动修改 PROJECT 中的语义内容。

Project Knowledge Promotion 仍由 Agent 完成。

# 35. `plan doctor`

检查：

```
.planning 是否存在

INDEX 是否存在

Active release path 是否有效

是否存在非法 Planning filename

PLAN 是否符合基本 section schema

是否存在多个 Active Release

INDEX Next Action 是否为空

文件是否超过容量预算
```

# 36. 推荐仓库结构

Skill Repository（canonical 源放在 `.agents/skills/planscope/`，
Codex / opencode / Kimi Code 原生发现该路径；Claude Code 由
`install.py` 同步到 `.claude/skills/planscope/`）：

```
Planscope/
│
├── README.md
├── LICENSE
├── skill-development-plan.md
├── docs/
│   └── compatibility.md        # 四工具兼容矩阵
│
├── .agents/skills/planscope/
│   ├── SKILL.md
│   │
│   ├── templates/
│   │   ├── INDEX.md
│   │   ├── PROJECT.md
│   │   ├── ROADMAP.md
│   │   ├── PLAN.md
│   │   ├── KNOWLEDGE.md
│   │   ├── LOG.md
│   │   └── SUMMARY.md
│   │
│   └── scripts/
│       ├── plan.py
│       └── spwf/
│           ├── core.py
│           └── commands.py
│
├── install.py                  # 同步到各工具 skill 目录
│
└── tests/
    ├── conftest.py
    ├── test_compat.py          # 四工具 frontmatter 合规
    ├── test_init.py
    ├── test_status.py
    ├── test_close.py
    └── test_doctor.py
```

# 37. Canonical SKILL.md Draft

推荐第一版保持极简。

```
---
name: planscope
description: >
  Scoped file-based planning for long-running software projects.
  Maintains a small active working set through INDEX routing,
  release-scoped plans, selective knowledge loading, rolling logs,
  compaction, and release archiving. Use for multi-step development,
  ongoing projects, release planning, complex debugging, or work that
  needs durable context across sessions. Small local changes should
  bypass planning whenever possible.
allowed-tools: Read Write Edit Bash Glob Grep
---

# Scoped Planning with Files

Use persistent project files as durable memory without loading the
entire project history into context.

The primary rule is:

> Keep the active working set small.

## Planning Root

All planning state lives under:

`.planning/`

Only the following planning filenames are allowed:

- `INDEX.md`
- `PROJECT.md`
- `ROADMAP.md`
- `PLAN.md`
- `KNOWLEDGE.md`
- `LOG.md`
- `SUMMARY.md`

Do not invent additional planning filenames.

## Context Routing

Do not read all planning files automatically.

Before loading planning context, classify the current task.

### Micro changes

Examples:

- typo fixes
- small CSS changes
- simple renames
- obvious local configuration edits

Planning may be skipped entirely.

If project context might matter, read only `.planning/INDEX.md`.

Do not update planning files unless the change affects the current
release state, project constraints, or future work.

### Local changes

Read:

1. `.planning/INDEX.md`
2. the relevant section of the active `PLAN.md`

Read `KNOWLEDGE.md` only when existing release knowledge is relevant.

### Feature or complex development

Read:

1. `.planning/INDEX.md`
2. active release `PLAN.md`
3. relevant sections of active release `KNOWLEDGE.md`

Read `PROJECT.md` only when architecture or stable project constraints matter.

### Planning or recovery

Read:

1. `INDEX.md`
2. active `PLAN.md`
3. relevant `KNOWLEDGE.md`
4. recent `LOG.md` content when execution continuity matters

Inspect Git state when useful.

Never automatically read archive content.

## File Responsibilities

### INDEX.md

The small routing document.

It contains:

- active release
- current focus
- current phase
- next action
- blockers
- context map
- critical constraints

Keep it concise.

### PROJECT.md

Stable cross-release project knowledge.

Use for:

- architecture
- long-term constraints
- stable conventions
- durable domain knowledge
- long-term decisions

Do not store temporary task or release information here.

### ROADMAP.md

High-level future direction only.

Do not put implementation details or task checklists here.

### PLAN.md

The active release plan.

It should mostly describe unfinished work.

Completed phases should be compressed into short summaries.

### KNOWLEDGE.md

Store information only when future work may need it and it cannot be
reliably recovered from ordinary source files.

Before writing a finding, ask:

"If this context disappeared, could a future agent make a wrong
decision because it did not know this?"

If no, do not record it.

Each important finding should use a stable ID:

`F-001`, `F-002`, ...

Allowed scopes:

- task
- release
- project

### LOG.md

A rolling execution log.

Keep only recent state, important validation, blockers, and temporary
context needed for recovery.

Do not duplicate Git history.

### SUMMARY.md

Created when a release closes.

It provides a compact historical overview so old PLAN, KNOWLEDGE, and
LOG files normally do not need to be reopened.

## IDs

Use stable IDs:

- Phase: `P1`, `P2`, ...
- Task: `T-001`, `T-002`, ...
- Finding: `F-001`, `F-002`, ...
- Decision: `D-001`, `D-002`, ...

Do not create custom ID formats.

## Update Rules

After meaningful progress:

- update PLAN when task or phase state changes
- update INDEX when current focus or next action changes
- update KNOWLEDGE only for reusable knowledge
- update LOG only when recent execution context is worth preserving

Do not write planning files merely because a tool was used.

## Completed Work

Plans are future-oriented.

When a phase completes, replace verbose completed checklists with a
short summary and references to important findings or decisions.

Do not allow completed work to dominate the active PLAN.

## Compaction

Compact planning files when they become large or repetitive.

During compaction:

- summarize completed PLAN phases
- merge duplicate findings
- remove obsolete task-scoped knowledge
- promote durable project knowledge when appropriate
- rotate old LOG content
- refresh INDEX

Preserve information that would affect future decisions.

## Release Closing

When the active release is complete:

1. verify its acceptance criteria
2. create SUMMARY.md
3. review KNOWLEDGE.md
4. promote durable project-scoped knowledge into PROJECT.md
5. archive release planning files
6. update ROADMAP.md
7. update INDEX.md

Archived releases must not remain part of the default working context.

## Recovery

After context loss or a new session:

1. read INDEX.md
2. read the active PLAN.md
3. inspect Git state if useful
4. search relevant KNOWLEDGE.md
5. read recent LOG.md only if necessary
6. continue from the recorded next action

Do not recover by loading all planning history.

## Core Principle

Persistent memory is not the same as active context.

Store information durably, but return only relevant information to the
working context.
```

# 38. INDEX Template

```
# Planning Index

## Active Release

[version or none]

Path:

[release path]

## Current Focus

[task ID and short description]

## Current Phase

[phase ID and title]

## Next Action

[single concrete next action]

## Current Blockers

None.

## Context Map

Project:
PROJECT.md

Roadmap:
ROADMAP.md

Active Plan:
[release]/PLAN.md

Active Knowledge:
[release]/KNOWLEDGE.md

Recent Log:
[release]/LOG.md

## Critical Constraints

- [only constraints immediately relevant to active work]
```

# 39. PLAN Template

```
# Release [version]

## Objective

[one clear release objective]

## Acceptance Criteria

- [verifiable criterion]
- [verifiable criterion]

## Status

in_progress

## Current

Phase:
P1

Task:
T-001

## Phases

### P1 [title]

Status:
in_progress

Tasks:

- [ ] T-001 [task]
- [ ] T-002 [task]

### P2 [title]

Status:
pending

Tasks:

- [ ] T-003 [task]

## Blockers

None.

## Next Action

T-001 [single concrete action]
```

# 40. KNOWLEDGE Template

```
# Release Knowledge

## F-001

Title:
[short title]

Scope:
task | release | project

Related:
[T-xxx / Pn / D-xxx]

Finding:

[knowledge worth preserving]

Source:

[file / documentation / experiment]

Impact:

[why future work should care]
```

# 41. LOG Template

```
# Work Log

## Current State

Phase:
[Pn]

Task:
[T-xxx]

Next:
[next action]

Blockers:
None.

## Recent Activity

### [date]

Completed:

[important work]

Validation:

[important validation only]

Result:

[pass / fail / partial]

Promoted:

[F-xxx / D-xxx if applicable]
```

# 42. SUMMARY Template

```
# Release [version] Summary

## Objective

[objective]

## Delivered

- [major result]

## Important Decisions

- D-xxx ...

## Promoted Project Knowledge

- ...

## Known Limitations

- ...

## Follow-Up Candidates

- ...
```

# 43. Agent 行为原则

整个 Skill 最终应该收敛成六个动作：

```
ROUTE
PLAN
RECORD
COMPACT
CLOSE
RECOVER
```

### ROUTE

先判断需要多少 Context。

### PLAN

维护当前 Release 的未来工作。

### RECORD

只保存未来真正可能重新需要的信息。

### COMPACT

不断缩小 Active Working Set。

### CLOSE

完成 Release 后 Promote + Archive。

### RECOVER

从最小必要上下文恢复，而不是加载所有历史。

# 44. 信息生命周期

整个项目的信息生命周期：

```
                  New Information
                         │
                         ▼
                 Is it reusable?
                   /           \
                 no             yes
                 │               │
                 ▼               ▼
            transient        KNOWLEDGE
                 │               │
                LOG          Determine Scope
                                │
                  ┌─────────────┼─────────────┐
                  ▼             ▼             ▼
                task          release       project
                  │             │             │
                drop         archive       promote
```

这应该成为整个 Skill 的核心信息模型。

# 45. Context 生命周期

Planning 文件存在，不代表它应该进入 Context。

```
Archive Storage
      │
      │ search when needed
      ▼
Durable Knowledge
      │
      │ route relevant pieces
      ▼
Active Release
      │
      │ select working set
      ▼
Agent Context
```

核心原则：

> Storage 可以不断增长，Working Context 不应该不断增长。

# 46. 第一版开发范围

v1.0 推荐只实现：

```
目录和文档规范
Canonical SKILL.md
Templates
Context Routing Rules
Micro Change Bypass
Compact Protocol
Release Close Protocol
Recovery Protocol
plan status
plan doctor
plan close
```

不要第一版实现：

```
自动知识摘要模型
JSON State
Database
Vector Search
DAG
Multi-Agent Coordinator
复杂 Hook System
Transcript Parsing
```

优先验证这套 Context Model 本身是否解决实际问题。

# 47. v1.0 验收标准

一个 Release 的长期开发过程中，应满足：

### Context

普通局部修改不会加载整个 Planning 系统。

### PLAN

完成任务不会导致 PLAN 无限增长。

### KNOWLEDGE

内容以可复用知识为主，而不是工具执行历史。

### LOG

LOG 大小长期保持在固定范围附近。

### Archive

过去 Release 不会进入默认 Context。

### Recovery

新 Session 可以通过：

```
INDEX
+
PLAN
+
selective knowledge
```

恢复当前工作。

### Naming

项目不会出现未经定义的 Planning 文件。

### Format

Agent 在不同 Session 中产生的 Planning 文档结构基本一致。

### Maintenance

Planning 文档维护应随着项目增长保持近似固定成本，而不是线性增长。

# 48. 后续可能的 v2

只有当 v1 的实际使用证明需要以后，再考虑：

```
state.json
machine-readable PLAN
event ledger
context compiler
semantic knowledge search
automatic compaction
multi-agent ownership
verification engine
```

这些能力可以作为 Runtime Layer 增加。

但它们不应该进入 v1 的核心设计。

# 49. 项目定位总结

传统 File Planning：

```
Write everything
→ Read everything
→ Context grows forever
```

Scoped Planning：

```
Store by lifecycle
→ Route by task
→ Load only relevant context
→ Compact completed work
→ Archive inactive releases
```

核心区别不是：

> 是否把上下文写入文件。

而是：

> **是否拥有明确的信息边界、生命周期和 Context Routing。**

# 50. 项目口号

推荐：

> **Persistent memory. Small working context.**

或者：

> **Store everything worth keeping. Load only what matters now.**

中文可以表达为：

> **长期保存，按需加载。**

最终核心原则：

> **Persistent memory is not active context.**

文件可以保存整个项目的历史。

Agent 当前需要看到的，只应该是完成眼前工作所需要的最小集合。
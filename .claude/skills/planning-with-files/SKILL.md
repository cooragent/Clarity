---
name: planning-with-files
version: "2.1.2"
description: 采用三文件（task_plan/findings/progress）进行外部记忆与阶段规划。
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - WebFetch
  - WebSearch
---

# Planning with Files

使用三文件作为“外部记忆”：

- `task_plan.md`：阶段计划与状态
- `findings.md`：研究发现与决策依据
- `progress.md`：过程日志与测试记录

## 文件位置

模板位于本技能目录的 `templates/`，实际规划文件应创建在项目根目录。

## 使用要点

- 复杂任务开始前先创建三文件
- 每完成一个阶段更新 `task_plan.md`
- 每发现新信息更新 `findings.md`
- 过程细节持续记录到 `progress.md`

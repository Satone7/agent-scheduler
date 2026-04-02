# Agent Scheduler Spec

## Why
用户需要一个基于动态配置的 Agent 调度器系统，用于管理复杂任务的执行流程。通过主 Agent 和子 Agent 的分离，以及基于独立上下文和 worktree 的隔离机制，可以实现更稳定、可回溯和灵活的任务调度与容错重试机制，防止执行环境被意外破坏。

## What Changes
- 设计并实现一个核心调度器引擎，负责接收和执行动态配置。
- 实现主 Agent（流程把控者）的生命周期管理：
  - 每次启动时清空上下文。
  - 初始化时加载上一次主 Agent 设置的提示词以及调度器的默认规则和必要文件保存路径。
  - 选择合适的 SKILL，根据需求制定子 Agent 的任务属性（提示词、模型、执行时间等）并注册到调度器。
  - 制定下一次唤起自身的提示词并注册到调度器，随后主动退出。
- 实现子 Agent（任务执行者）的隔离执行：
  - 通过 `claude --worktree` 的方式启动，执行主 Agent 布置的具体任务。
  - 任务失败时，调度器能够废弃当前子 Agent 的变更记录，重新执行或流转。
- 确保在子 Agent 任务结束或执行时间耗尽时，准确唤起主 Agent。

## Impact
- Affected specs: 调度器核心控制流、Agent 无状态生命周期管理、Worktree 任务隔离机制。
- Affected code: 将从零构建整个项目架构，核心模块包括：`scheduler`（调度器引擎）、`agent_manager`（主/子 Agent 封装）、`config`（配置和规则注入）、`worktree_runner`（执行环境隔离）等。

## ADDED Requirements
### Requirement: 主 Agent 的无状态化执行机制
系统必须支持主 Agent 每次基于纯净上下文启动并动态生成后续配置。
#### Scenario: 主 Agent 下发任务并退出
- **WHEN** 用户输入初始需求，或子 Agent 任务完成/超时触发下一次主 Agent 唤醒时
- **THEN** 调度器清空主 Agent 的上下文并以默认规则和前置提示词启动；主 Agent 制定出子 Agent 配置（含模型、时间等）及下次主 Agent 的唤醒提示词，全部注册到调度器后退出。

### Requirement: 子 Agent 隔离与容错机制
系统必须确保子 Agent 的所有执行过程被隔离，并在失败时能自动清理。
#### Scenario: 子 Agent 任务执行失败
- **WHEN** 子 Agent 在 `claude --worktree` 环境下执行任务失败
- **THEN** 调度器直接丢弃该 worktree 产生的全部变更，不对主干产生任何影响，并且可以选择重新执行或重新唤醒主 Agent 处置异常。

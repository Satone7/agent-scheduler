# Agent Scheduler 框架

Agent Scheduler 是一个用于编排和调度自治 Agent（智能体）的轻量级 Python 框架。它通过主从 Agent 架构（Main/Sub Agent）、严格的 YAML 工作流校验以及基于 Git 的安全执行沙箱，帮助开发者构建复杂、可靠的多步骤自动化流程。

## 🌟 核心特性

- **基于 YAML 的工作流定义**：通过简单的 YAML 文件定义状态机（Phases）、流转规则（Transitions）以及依赖的上下文数据（Required Memory）。
- **主/子 Agent 协同调度**：主 Agent 负责拆解任务、管理上下文和决策状态流转；调度引擎将子任务分配给 Worktree Runner 执行。
- **安全的沙箱执行机制**：`WorktreeRunner` 支持执行超时控制。如果子任务执行失败或崩溃，框架会自动使用 `git reset --hard` 和 `git clean -fd` 恢复工作区环境，防止意外破坏代码库。
- **严格的状态校验**：`WorkflowValidator` 会在每次状态流转前拦截非法操作，确保必填上下文（Memory）完备以及流转路径合法。

## 🚀 快速开始

### 1. 环境准备

确保您的环境中已安装所需的依赖：

```bash
pip install -r requirements.txt
```

### 2. 基础使用示例

以下是如何将调度引擎、验证器和主 Agent 组合使用的基本示例：

```python
from scheduler import SchedulerEngine
from workflow_validator import WorkflowValidator
from main_agent import MainAgent
from worktree_runner import WorktreeRunner

# 1. 加载工作流定义并初始化验证器
validator = WorkflowValidator("sample_workflow.yaml")

# 2. 初始化调度器引擎，并注入验证器
scheduler = SchedulerEngine(workflow_validator=validator)
scheduler.start()

# 3. 初始化主 Agent，绑定调度器
main_agent = MainAgent(scheduler=scheduler, default_save_path="/workspace")

# 4. 触发主 Agent 唤醒并下发初始 Prompt
scheduler.set_next_wakeup_prompt("初始化工作流并开始执行任务")
scheduler.trigger_main_agent_wakeup(main_agent.wakeup)

# 5. （可选）使用 WorktreeRunner 执行生成的子任务
runner = WorktreeRunner()
for task in scheduler.sub_agent_tasks:
    runner.run_task(task, timeout_seconds=3600)
```

## 🛠️ 如何定义自己的工作流

您可以完全通过 YAML 文件来定义自己的业务流程。工作流被拆分为多个**阶段 (Phases)**，每个阶段都可以配置其描述、允许的下一阶段以及必须具备的上下文记忆（Memory）。

### 配置文件结构

创建一个 YAML 文件（例如 `custom_workflow.yaml`），其核心结构如下：

```yaml
name: "YourWorkflowName"
description: "工作流的整体描述"
version: "1.0"
phases:
  # 阶段 1：初始化
  init:
    description: "初始化阶段，准备必要的数据"
    next_phases:
      - process  # 允许流转到的下一个阶段
    required_memory: [] # 进入该阶段所需的上下文变量键名
  
  # 阶段 2：处理
  process:
    description: "核心处理阶段"
    next_phases:
      - review
    required_memory:
      - input_data  # 必须在上下文中包含 input_data 才能进入此阶段
  
  # 阶段 3：审核
  review:
    description: "审核结果"
    next_phases:
      - process  # 可以打回重新处理
      - publish  # 也可以流转到发布
    required_memory:
      - processed_result
```

### 字段说明：
- **`phases`**: 包含工作流所有可能阶段的字典。
- **`description`**: 阶段的文字描述，可供大模型或开发者理解该阶段的目的。
- **`next_phases`**: 一个列表，明确规定了**当前阶段只能流转到列表中的哪些阶段**。如果尝试流转到未定义的阶段，`WorkflowValidator` 将抛出 `InvalidTransitionError` 异常。
- **`required_memory`**: 一个列表，声明了**要进入该阶段，共享内存（Shared Memory）中必须存在的字段**。这保证了前置任务已正确输出了必要的数据，避免流程出错。

### 参考示例：文章撰写工作流
您可以参考项目中的 `sample_workflow.yaml`，了解真实场景下的配置：

```yaml
name: "ArticleWritingSkill"
version: "1.0"
phases:
  plan:
    description: "Plan the article structure based on the topic."
    next_phases: 
      - draft
    required_memory: 
      - topic
      - outline
  draft:
    description: "Write the first draft of the article."
    next_phases: 
      - review
    required_memory: 
      - draft_content
  review:
    description: "Review and refine the draft."
    next_phases: 
      - publish
      - draft
    required_memory: 
      - feedback
  publish:
    description: "Publish the final article."
    next_phases: []
    required_memory: 
      - final_content
```

## 🧩 核心组件架构说明

- [**`SchedulerEngine`**](file:///workspace/scheduler.py)：整个框架的心脏。负责维护系统状态、管理全局配置、暂存子 Agent 任务队列，并处理状态更新。
- [**`MainAgent`**](file:///workspace/main_agent.py)：相当于工作流的“大脑”。它在每次被唤醒时获取当前上下文，并决策：下一步该生成哪些子任务？工作流该流转到哪个阶段？
- [**`WorktreeRunner`**](file:///workspace/worktree_runner.py)：负责在子进程中调用命令行（如 `claude --worktree`）执行具体任务。它内置了安全机制，遇到执行失败会通过 Git 命令回滚工作区。
- [**`WorkflowValidator`**](file:///workspace/workflow_validator.py)：规则守护者。在主 Agent 提交状态更新时拦截请求，比对 YAML 规则，防止工作流陷入错误或死锁状态。
- [**`Models`**](file:///workspace/models.py)：定义了所有核心的数据结构，如 `AgentTask`, `WorkflowState`, `AgentStateUpdate` 等。

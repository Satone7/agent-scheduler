# Tasks
- [x] Task 1: 初始化项目结构和领域模型设计
  - [x] SubTask 1.1: 定义调度器配置、状态存储结构（SchedulerConfig, SchedulerState）。
  - [x] SubTask 1.2: 定义主 Agent 提示词载体、子 Agent 任务描述（AgentTask）等核心数据模型。
- [x] Task 2: 实现核心调度器引擎 (Scheduler Engine)
  - [x] SubTask 2.1: 实现配置注册表（接收主 Agent 生成的子 Agent 配置和下次唤醒提示词）。
  - [x] SubTask 2.2: 实现主 Agent 的唤醒触发机制与退出逻辑。
- [x] Task 3: 实现 Worktree 执行环境封装 (Worktree Runner)
  - [x] SubTask 3.1: 封装命令行接口，支持以 `claude --worktree` 方式启动子 Agent 并传递任务参数。
  - [x] SubTask 3.2: 实现子 Agent 执行监控、超时控制及执行失败后的变更废弃清理逻辑。
- [x] Task 4: 实现主 Agent 上下文管理及规则注入
  - [x] SubTask 4.1: 实现每次唤醒主 Agent 时的上下文环境重置和前置提示词注入。
  - [x] SubTask 4.2: 将调度器默认规则、文件保存路径等系统级参数整合注入给主 Agent。
- [x] Task 5: 系统集成测试与容错验证
  - [x] SubTask 5.1: 编写核心控制流的端到端测试（主 Agent 启动 -> 下发任务 -> 子 Agent 执行 -> 主 Agent 再次唤醒）。
  - [x] SubTask 5.2: 针对子 Agent 失败场景，验证隔离环境的变更丢弃和重试机制是否生效。

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 1
- Task 4 depends on Task 2
- Task 5 depends on Task 2, Task 3, Task 4

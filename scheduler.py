import logging
from typing import List, Optional, Callable, Dict, Any
from models import AgentTask, SchedulerConfig, SchedulerState, SchedulerStatus, TaskStatus, WorkflowState, AgentStateUpdate

logger = logging.getLogger(__name__)

class SchedulerEngine:
    """
    核心调度器引擎
    """
    def __init__(self, workflow_validator: Optional[Any] = None):
        self.config_registry: Dict[str, SchedulerConfig] = {}
        self.default_config: Optional[SchedulerConfig] = None
        self.state = SchedulerState()
        self.sub_agent_tasks: List[AgentTask] = []
        self.next_wakeup_prompt: Optional[str] = None
        self._is_running = False
        
        self.workflow_state = WorkflowState()
        self.workflow_validator = workflow_validator

    def register_config(self, name: str, config: SchedulerConfig, set_as_default: bool = False):
        """
        提供配置注册表功能
        """
        self.config_registry[name] = config
        if set_as_default or self.default_config is None:
            self.default_config = config
        logger.info(f"Registered configuration '{name}'.")

    def get_config(self, name: Optional[str] = None) -> SchedulerConfig:
        """
        获取配置，如果没有指定名称，则返回默认配置
        """
        if name and name in self.config_registry:
            return self.config_registry[name]
        if self.default_config:
            return self.default_config
        return SchedulerConfig() # return a new default if none registered

    def receive_sub_agent_tasks(self, tasks: List[AgentTask]):
        """
        接收并存储主 Agent 生成的子 Agent 配置 (AgentTask)
        """
        self.sub_agent_tasks.extend(tasks)
        self.state.queued_tasks += len([t for t in tasks if t.status == TaskStatus.PENDING])
        logger.info(f"Received {len(tasks)} sub-agent tasks. Total queued: {self.state.queued_tasks}")

    def set_next_wakeup_prompt(self, prompt: str):
        """
        接收并存储下一次主 Agent 唤醒的提示词
        """
        self.next_wakeup_prompt = prompt
        logger.info("Set next wakeup prompt for main Agent.")

    def trigger_main_agent_wakeup(self, wakeup_callback: Callable[[str, List[AgentTask]], None]):
        """
        实现主 Agent 的唤醒触发机制
        """
        if not self._is_running:
            logger.warning("Scheduler is not running, cannot trigger wakeup.")
            return False

        if not self.next_wakeup_prompt:
            logger.warning("No wakeup prompt set, cannot trigger main Agent.")
            return False

        logger.info("Triggering main Agent wakeup.")
        try:
            # 传递提示词和当前的子 Agent 任务列表给主 Agent
            current_prompt = self.next_wakeup_prompt
            # 唤醒前，清理当前提示词，以便主 Agent 设置下一次提示词
            self.next_wakeup_prompt = None
            wakeup_callback(current_prompt, self.sub_agent_tasks)
            return True
        except Exception as e:
            logger.error(f"Error occurred during main Agent wakeup: {e}")
            return False

    def start(self):
        """
        启动调度器
        """
        if self._is_running:
            logger.warning("Scheduler is already running.")
            return
        
        self._is_running = True
        self.state.status = SchedulerStatus.RUNNING
        logger.info("Scheduler started.")

    def stop(self):
        """
        实现退出逻辑
        """
        if not self._is_running:
            logger.warning("Scheduler is not running.")
            return

        self._is_running = False
        self.state.status = SchedulerStatus.STOPPED
        logger.info("Scheduler stopped.")

    @property
    def is_running(self) -> bool:
        return self._is_running

    def update_workflow_state(self, update_request: AgentStateUpdate):
        """
        处理主 Agent 提交的状态更新。
        首先使用 Validator 进行合法性校验，通过后更新托管的 WorkflowState。
        """
        if self.workflow_validator:
            import workflow_validator as wv
            # Validator 需要目标阶段。如果未提供 next_stage，我们将其视作停留在当前阶段
            target_phase = update_request.next_stage or self.workflow_state.current_stage
            
            val_state = wv.WorkflowState(
                current_phase=self.workflow_state.current_stage,
                memory=self.workflow_state.shared_memory
            )
            val_update = wv.AgentStateUpdate(
                target_phase=target_phase,
                updates_to_memory=update_request.updates_to_memory
            )
            
            # 进行合法性校验，如果校验失败会抛出异常
            self.workflow_validator.validate(val_state, val_update)

        # 校验通过（或没有配置 Validator），更新托管的 WorkflowState
        if update_request.next_stage and update_request.next_stage != self.workflow_state.current_stage:
            # 记录 completed_stages
            self.workflow_state.completed_stages.append(self.workflow_state.current_stage)
            # 修改 current_stage
            self.workflow_state.current_stage = update_request.next_stage
            
        # 合并 shared_memory
        if update_request.updates_to_memory:
            self.workflow_state.shared_memory.update(update_request.updates_to_memory)
            
        logger.info(f"Workflow state updated. Current stage: {self.workflow_state.current_stage}")

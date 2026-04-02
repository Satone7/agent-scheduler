import logging
from typing import List, Optional, Callable, Dict, Any
from models import AgentTask, SchedulerConfig, SchedulerState, SchedulerStatus, TaskStatus

logger = logging.getLogger(__name__)

class SchedulerEngine:
    """
    核心调度器引擎
    """
    def __init__(self):
        self.config_registry: Dict[str, SchedulerConfig] = {}
        self.default_config: Optional[SchedulerConfig] = None
        self.state = SchedulerState()
        self.sub_agent_tasks: List[AgentTask] = []
        self.next_wakeup_prompt: Optional[str] = None
        self._is_running = False

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

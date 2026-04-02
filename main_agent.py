import logging
import dataclasses
from typing import List, Dict, Any, Optional
from models import AgentTask, SchedulerConfig
from scheduler import SchedulerEngine

logger = logging.getLogger(__name__)

class MainAgent:
    """
    主 Agent
    负责上下文管理和规则注入，协调子任务生成与调度。
    """
    def __init__(self, scheduler: SchedulerEngine, default_save_path: str = "/workspace"):
        self.scheduler = scheduler
        self.default_save_path = default_save_path
        self.context: Dict[str, Any] = {}
        
        # 默认调度器规则
        self.default_rules = [
            "1. Analyze the current environment and task requirements.",
            "2. Break down complex tasks into manageable sub-agent tasks.",
            "3. Ensure all generated tasks have clear descriptions and objectives.",
            "4. Provide a comprehensive prompt for the next wakeup cycle."
        ]

    def _clear_context(self):
        """清空之前的上下文"""
        self.context.clear()
        logger.debug("Main Agent context cleared.")

    def _inject_rules_and_context(self, previous_prompt: str):
        """注入默认调度器规则、文件保存路径及上一次配置的提示词"""
        self.context = {
            "rules": self.default_rules,
            "save_path": self.default_save_path,
            "previous_prompt": previous_prompt,
            "scheduler_config": dataclasses.asdict(self.scheduler.get_config())
        }
        logger.debug(f"Injected rules, save path: {self.default_save_path}, and previous prompt.")

    def _generate_next_tasks(self, prompt: str, current_tasks: List[AgentTask]) -> List[AgentTask]:
        """
        根据输入输出生成下一步的配置(子任务)
        此处为模拟逻辑，实际应用中会调用大模型生成任务
        """
        logger.info(f"Generating tasks based on prompt: '{prompt}'")
        new_tasks = []
        if "init" in prompt.lower():
            new_tasks.append(AgentTask(name="Initial Setup", description="Perform initial setup tasks."))
        elif "analyze" in prompt.lower():
            new_tasks.append(AgentTask(name="Code Analysis", description="Analyze the current codebase."))
        else:
            new_tasks.append(AgentTask(name="Follow-up Action", description=f"Action derived from: {prompt}"))
        
        return new_tasks

    def _generate_next_prompt(self, prompt: str, current_tasks: List[AgentTask]) -> str:
        """
        根据输入输出生成下一步的提示词
        此处为模拟逻辑，实际应用中会调用大模型生成
        """
        return f"Continue processing after executing tasks derived from: '{prompt}'"

    def wakeup(self, prompt: str, current_tasks: List[AgentTask]) -> None:
        """
        主 Agent 唤醒回调函数。
        
        1. 清空之前的上下文
        2. 注入默认调度器规则、文件保存路径及上一次配置的提示词
        3. 根据输入输出生成下一步的配置和提示词
        4. 将生成的任务和提示词回写到调度器中
        """
        logger.info("Main Agent awakened.")
        
        # 1. 每次被唤醒时清空之前的上下文
        self._clear_context()
        
        # 2. 注入默认调度器规则、文件保存路径及上一次配置的提示词
        self._inject_rules_and_context(prompt)
        
        # 3. 根据输入输出生成下一步的配置和提示词
        new_tasks = self._generate_next_tasks(prompt, current_tasks)
        next_prompt = self._generate_next_prompt(prompt, current_tasks)
        
        # 4. 将生成的任务交给调度器
        if new_tasks:
            self.scheduler.receive_sub_agent_tasks(new_tasks)
            
        # 5. 设置下一次唤醒的提示词
        self.scheduler.set_next_wakeup_prompt(next_prompt)
        
        logger.info("Main Agent sleep.")


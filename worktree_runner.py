import os
import subprocess
import logging
import datetime
from typing import Optional, List

from models import AgentTask, TaskStatus

logger = logging.getLogger(__name__)

class WorktreeRunner:
    """
    封装命令接口，支持通过 subprocess 启动 `claude --worktree` 唤起子 Agent。
    实现子 Agent 的执行监控、超时控制，及执行失败时的变更废弃清理（恢复环境）逻辑。
    """

    def __init__(self, cwd: Optional[str] = None):
        """
        :param cwd: 工作目录。如果不提供，默认为当前目录。
        """
        self.cwd = cwd or os.getcwd()

    def build_command(self, task: AgentTask) -> List[str]:
        """
        构建唤起子 Agent 的命令。
        根据需求，命令固定前缀为 `claude --worktree`。
        可根据 task 中的 payload 提取具体的提示词或参数。
        """
        cmd = ["claude", "--worktree"]
        
        # 尝试从 payload 中提取执行参数，若无则使用 description 作为默认的 prompt
        prompt = task.payload.get("prompt") or task.description
        if prompt:
            cmd.extend(["--prompt", prompt])
            
        return cmd

    def run_task(self, task: AgentTask, timeout_seconds: int = 3600) -> bool:
        """
        执行子 Agent 任务。包含执行监控、超时控制和失败环境恢复。
        
        :param task: 任务实例
        :param timeout_seconds: 超时时间，默认 3600 秒
        :return: 执行是否成功
        """
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.datetime.now(datetime.timezone.utc)
        cmd = self.build_command(task)
        
        logger.info(f"Starting sub-agent for task {task.task_id} with cmd: {' '.join(cmd)}")
        
        success = False
        try:
            result = subprocess.run(
                cmd,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=True
            )
            # 执行成功
            task.result = result.stdout
            task.status = TaskStatus.COMPLETED
            success = True
            logger.info(f"Task {task.task_id} completed successfully.")
            
        except subprocess.TimeoutExpired as e:
            # 超时控制
            error_msg = f"Task {task.task_id} timed out after {timeout_seconds} seconds. Output: {e.stdout}"
            logger.error(error_msg)
            task.error = error_msg
            task.status = TaskStatus.FAILED
            self._cleanup_environment()
            
        except subprocess.CalledProcessError as e:
            # 执行失败
            error_msg = f"Task {task.task_id} failed with exit code {e.returncode}. Error: {e.stderr}"
            logger.error(error_msg)
            task.error = error_msg
            task.status = TaskStatus.FAILED
            self._cleanup_environment()
            
        except Exception as e:
            # 其他异常
            error_msg = f"Task {task.task_id} encountered an unexpected error: {str(e)}"
            logger.error(error_msg)
            task.error = error_msg
            task.status = TaskStatus.FAILED
            self._cleanup_environment()
            
        finally:
            task.completed_at = datetime.datetime.now(datetime.timezone.utc)
            
        return success

    def _cleanup_environment(self) -> None:
        """
        执行失败时的变更废弃清理（恢复环境）逻辑。
        通过 git reset 和 git clean 将工作区恢复到纯净状态，以防执行环境被意外破坏。
        """
        logger.warning(f"Task failed. Cleaning up environment in {self.cwd}...")
        try:
            # 放弃所有 tracked 文件的修改
            subprocess.run(
                ["git", "reset", "--hard", "HEAD"],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                check=True
            )
            # 删除所有 untracked 的文件和目录
            subprocess.run(
                ["git", "clean", "-fd"],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Environment cleanup successful.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to cleanup environment: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error during cleanup: {str(e)}")

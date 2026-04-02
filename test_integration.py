import pytest
import subprocess
from unittest.mock import MagicMock, patch

from scheduler import SchedulerEngine
from main_agent import MainAgent
from worktree_runner import WorktreeRunner
from models import TaskStatus

@patch("subprocess.run")
def test_end_to_end_successful_flow(mock_run):
    """
    验证主 Agent 启动、下发任务、子 Agent 隔离执行成功的完整控制流。
    """
    # 1. 初始化各组件
    scheduler = SchedulerEngine()
    main_agent = MainAgent(scheduler, default_save_path="/workspace")
    runner = WorktreeRunner(cwd="/workspace")

    # 模拟 subprocess.run 执行成功
    mock_result = MagicMock()
    mock_result.stdout = "Task executed successfully."
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    # 2. 验证主 Agent 启动
    scheduler.start()
    assert scheduler.is_running is True

    # 3. 设置下一次唤醒提示词并触发唤醒，验证下发任务
    scheduler.set_next_wakeup_prompt("init the project")
    success = scheduler.trigger_main_agent_wakeup(main_agent.wakeup)
    
    assert success is True
    # 主 Agent 会根据提示词生成任务并放回调度器
    assert len(scheduler.sub_agent_tasks) > 0
    task = scheduler.sub_agent_tasks[0]
    assert task.status == TaskStatus.PENDING

    # 4. 验证子 Agent 隔离执行 (成功情况)
    result = runner.run_task(task)
    
    # 验证执行结果
    assert result is True
    assert task.status == TaskStatus.COMPLETED
    assert task.result == "Task executed successfully."
    
    # 验证命令构造正确
    mock_run.assert_called_once()
    called_cmd = mock_run.call_args[0][0]
    assert called_cmd[0] == "claude"
    assert "--worktree" in called_cmd

@patch("subprocess.run")
def test_end_to_end_failure_rollback_flow(mock_run):
    """
    验证子 Agent 执行失败时，触发废弃清理(失败回滚)的完整控制流。
    """
    # 1. 初始化各组件
    scheduler = SchedulerEngine()
    main_agent = MainAgent(scheduler, default_save_path="/workspace")
    runner = WorktreeRunner(cwd="/workspace")

    # 2. 验证主 Agent 启动及下发任务
    scheduler.start()
    scheduler.set_next_wakeup_prompt("analyze the code with errors")
    scheduler.trigger_main_agent_wakeup(main_agent.wakeup)
    
    assert len(scheduler.sub_agent_tasks) > 0
    task = scheduler.sub_agent_tasks[0]
    assert task.status == TaskStatus.PENDING

    # 模拟 subprocess.run，当执行 claude 命令时失败，执行 git 恢复命令时成功
    def mock_subprocess_run(cmd, *args, **kwargs):
        if "claude" in cmd:
            raise subprocess.CalledProcessError(
                returncode=1, 
                cmd=cmd, 
                stderr="Execution failed due to syntax error."
            )
        else:
            # 针对 git reset 和 git clean 的模拟
            mock_proc = MagicMock()
            mock_proc.stdout = ""
            mock_proc.returncode = 0
            return mock_proc

    mock_run.side_effect = mock_subprocess_run

    # 3. 验证子 Agent 失败回滚的完整控制流
    result = runner.run_task(task)
    
    # 验证执行结果为失败，且状态被正确置为 FAILED
    assert result is False
    assert task.status == TaskStatus.FAILED
    assert "Execution failed due to syntax error" in task.error

    # 4. 验证是否正确执行了环境清理逻辑 (失败回滚)
    calls = mock_run.call_args_list
    assert len(calls) == 3, "Should call claude command, git reset, and git clean."
    
    # 验证具体调用顺序和命令内容
    assert "claude" in calls[0][0][0]
    assert calls[1][0][0] == ["git", "reset", "--hard", "HEAD"]
    assert calls[2][0][0] == ["git", "clean", "-fd"]

import unittest
from unittest.mock import patch, MagicMock
import subprocess
import datetime
from models import AgentTask, TaskStatus
from worktree_runner import WorktreeRunner

class TestWorktreeRunner(unittest.TestCase):

    def setUp(self):
        self.runner = WorktreeRunner(cwd="/fake/cwd")

    def test_build_command(self):
        task = AgentTask(description="Fix the bug")
        cmd = self.runner.build_command(task)
        self.assertEqual(cmd, ["claude", "--worktree", "--prompt", "Fix the bug"])
        
        task.payload = {"prompt": "Implement a new feature"}
        cmd = self.runner.build_command(task)
        self.assertEqual(cmd, ["claude", "--worktree", "--prompt", "Implement a new feature"])
        
        task.description = None
        task.payload = {}
        cmd = self.runner.build_command(task)
        self.assertEqual(cmd, ["claude", "--worktree"])

    @patch("subprocess.run")
    def test_run_task_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "Success output"
        mock_run.return_value = mock_result
        
        task = AgentTask(description="Fix the bug")
        
        success = self.runner.run_task(task)
        
        self.assertTrue(success)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertEqual(task.result, "Success output")
        self.assertIsNone(task.error)
        self.assertIsNotNone(task.started_at)
        self.assertIsNotNone(task.completed_at)
        
        mock_run.assert_called_once_with(
            ["claude", "--worktree", "--prompt", "Fix the bug"],
            cwd="/fake/cwd",
            capture_output=True,
            text=True,
            timeout=3600,
            check=True
        )

    @patch("subprocess.run")
    @patch.object(WorktreeRunner, "_cleanup_environment")
    def test_run_task_timeout(self, mock_cleanup, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=3600, output="Partial output")
        
        task = AgentTask(description="Time consuming task")
        
        success = self.runner.run_task(task)
        
        self.assertFalse(success)
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertIn("timed out", task.error)
        mock_cleanup.assert_called_once()

    @patch("subprocess.run")
    @patch.object(WorktreeRunner, "_cleanup_environment")
    def test_run_task_called_process_error(self, mock_cleanup, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd="claude", stderr="Syntax error")
        
        task = AgentTask(description="Failing task")
        
        success = self.runner.run_task(task)
        
        self.assertFalse(success)
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertIn("failed with exit code", task.error)
        mock_cleanup.assert_called_once()

    @patch("subprocess.run")
    def test_cleanup_environment(self, mock_run):
        self.runner._cleanup_environment()
        
        # Should call git reset and git clean
        self.assertEqual(mock_run.call_count, 2)
        mock_run.assert_any_call(
            ["git", "reset", "--hard", "HEAD"],
            cwd="/fake/cwd",
            capture_output=True,
            text=True,
            check=True
        )
        mock_run.assert_any_call(
            ["git", "clean", "-fd"],
            cwd="/fake/cwd",
            capture_output=True,
            text=True,
            check=True
        )

if __name__ == '__main__':
    unittest.main()

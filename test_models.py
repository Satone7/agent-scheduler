import unittest
from models import SchedulerConfig, SchedulerState, AgentTask, TaskStatus, SchedulerStatus

class TestModels(unittest.TestCase):
    def test_scheduler_config(self):
        config = SchedulerConfig(max_concurrent_tasks=10)
        self.assertEqual(config.max_concurrent_tasks, 10)
        self.assertEqual(config.retry_limit, 3) # default

    def test_scheduler_state(self):
        state = SchedulerState(status=SchedulerStatus.RUNNING)
        self.assertEqual(state.status, SchedulerStatus.RUNNING)
        self.assertEqual(state.active_tasks, 0) # default

    def test_agent_task(self):
        task = AgentTask(name="Test Task")
        self.assertIsNotNone(task.task_id)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.name, "Test Task")

if __name__ == '__main__':
    unittest.main()

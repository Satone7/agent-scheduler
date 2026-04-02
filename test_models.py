import unittest
from models import (
    SchedulerConfig, SchedulerState, AgentTask, TaskStatus, SchedulerStatus,
    WorkflowState, AgentStateUpdate
)
from pydantic import ValidationError

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

    def test_workflow_state(self):
        state = WorkflowState()
        self.assertEqual(state.current_stage, "init")
        self.assertEqual(state.completed_stages, [])
        self.assertEqual(state.shared_memory, {})

        state.current_stage = "processing"
        state.completed_stages.append("init")
        state.shared_memory["key"] = "value"
        self.assertEqual(state.current_stage, "processing")
        self.assertIn("init", state.completed_stages)
        self.assertEqual(state.shared_memory["key"], "value")

    def test_agent_state_update(self):
        update = AgentStateUpdate(action="process_data")
        self.assertEqual(update.action, "process_data")
        self.assertIsNone(update.next_stage)
        self.assertEqual(update.updates_to_memory, {})

        update_full = AgentStateUpdate(
            action="finish",
            next_stage="done",
            updates_to_memory={"result": 42}
        )
        self.assertEqual(update_full.action, "finish")
        self.assertEqual(update_full.next_stage, "done")
        self.assertEqual(update_full.updates_to_memory["result"], 42)

        with self.assertRaises(ValidationError):
            AgentStateUpdate()  # Missing required 'action'

if __name__ == '__main__':
    unittest.main()

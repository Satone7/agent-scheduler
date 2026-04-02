import unittest
from models import AgentTask, SchedulerConfig, SchedulerStatus, TaskStatus
from scheduler import SchedulerEngine

class TestSchedulerEngine(unittest.TestCase):
    def setUp(self):
        self.scheduler = SchedulerEngine()

    def test_config_registry(self):
        config1 = SchedulerConfig(max_concurrent_tasks=10)
        config2 = SchedulerConfig(max_concurrent_tasks=20)

        self.scheduler.register_config("config1", config1, set_as_default=True)
        self.scheduler.register_config("config2", config2)

        self.assertEqual(self.scheduler.get_config("config1").max_concurrent_tasks, 10)
        self.assertEqual(self.scheduler.get_config("config2").max_concurrent_tasks, 20)
        self.assertEqual(self.scheduler.get_config().max_concurrent_tasks, 10) # default

    def test_receive_sub_agent_tasks(self):
        task1 = AgentTask(name="task1", status=TaskStatus.PENDING)
        task2 = AgentTask(name="task2", status=TaskStatus.RUNNING)

        self.scheduler.receive_sub_agent_tasks([task1, task2])

        self.assertEqual(len(self.scheduler.sub_agent_tasks), 2)
        # 只有一个 PENDING 的任务应该增加 queued_tasks 的计数
        self.assertEqual(self.scheduler.state.queued_tasks, 1)

    def test_set_next_wakeup_prompt(self):
        prompt = "This is a wakeup prompt."
        self.scheduler.set_next_wakeup_prompt(prompt)
        self.assertEqual(self.scheduler.next_wakeup_prompt, prompt)

    def test_trigger_main_agent_wakeup(self):
        # 确保需要 running 才能触发
        self.scheduler.start()
        
        task1 = AgentTask(name="task1")
        self.scheduler.receive_sub_agent_tasks([task1])
        self.scheduler.set_next_wakeup_prompt("Wakeup main agent!")

        callback_called = False
        def main_agent_callback(prompt, tasks):
            nonlocal callback_called
            callback_called = True
            self.assertEqual(prompt, "Wakeup main agent!")
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].name, "task1")

        result = self.scheduler.trigger_main_agent_wakeup(main_agent_callback)
        self.assertTrue(result)
        self.assertTrue(callback_called)
        # 触发后应该清空
        self.assertIsNone(self.scheduler.next_wakeup_prompt)

    def test_trigger_wakeup_not_running(self):
        self.scheduler.set_next_wakeup_prompt("Wakeup main agent!")
        
        callback_called = False
        def main_agent_callback(prompt, tasks):
            nonlocal callback_called
            callback_called = True

        result = self.scheduler.trigger_main_agent_wakeup(main_agent_callback)
        self.assertFalse(result)
        self.assertFalse(callback_called)

    def test_start_stop(self):
        self.scheduler.start()
        self.assertTrue(self.scheduler.is_running)
        self.assertEqual(self.scheduler.state.status, SchedulerStatus.RUNNING)

        self.scheduler.stop()
        self.assertFalse(self.scheduler.is_running)
        self.assertEqual(self.scheduler.state.status, SchedulerStatus.STOPPED)

if __name__ == '__main__':
    unittest.main()

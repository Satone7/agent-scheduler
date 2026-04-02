import unittest
from workflow_validator import (
    WorkflowValidator,
    WorkflowState,
    AgentStateUpdate,
    PhaseNotFoundError,
    InvalidTransitionError,
    MissingRequiredMemoryError
)

class TestWorkflowValidator(unittest.TestCase):
    def setUp(self):
        # 使用我们刚创建的 sample_workflow.yaml
        self.validator = WorkflowValidator('sample_workflow.yaml')

    def test_valid_transition(self):
        """测试合法的状态流转和参数"""
        state = WorkflowState(current_phase="plan", memory={"topic": "AI Trends"})
        update = AgentStateUpdate(target_phase="draft", updates_to_memory={"draft_content": "This is a draft."})
        
        # 不应抛出异常
        self.assertTrue(self.validator.validate(state, update))

    def test_invalid_target_phase(self):
        """测试目标阶段不存在的情况"""
        state = WorkflowState(current_phase="plan", memory={"topic": "AI Trends"})
        update = AgentStateUpdate(target_phase="unknown_phase", updates_to_memory={})
        
        with self.assertRaises(PhaseNotFoundError):
            self.validator.validate(state, update)

    def test_invalid_transition(self):
        """测试非法的阶段流转"""
        # 从 plan 直接跳到 review 是不允许的，因为 plan 的 next_phases 只有 draft
        state = WorkflowState(current_phase="plan", memory={"topic": "AI Trends"})
        update = AgentStateUpdate(target_phase="review", updates_to_memory={"feedback": "Good"})
        
        with self.assertRaises(InvalidTransitionError):
            self.validator.validate(state, update)

    def test_missing_required_memory(self):
        """测试缺少必填字段的情况"""
        state = WorkflowState(current_phase="plan", memory={"topic": "AI Trends"})
        # draft 阶段要求 draft_content，但这里没提供
        update = AgentStateUpdate(target_phase="draft", updates_to_memory={})
        
        with self.assertRaises(MissingRequiredMemoryError):
            self.validator.validate(state, update)

    def test_required_memory_in_current_state(self):
        """测试必填字段已存在于当前状态内存中的情况"""
        # publish 要求 final_content
        state = WorkflowState(current_phase="review", memory={"final_content": "Final Article..."})
        update = AgentStateUpdate(target_phase="publish", updates_to_memory={})
        
        # 由于 final_content 已经在 state.memory 中，校验应该通过
        self.assertTrue(self.validator.validate(state, update))

if __name__ == '__main__':
    unittest.main()

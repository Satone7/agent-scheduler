from scheduler import SchedulerEngine
from main_agent import MainAgent
from workflow_validator import WorkflowValidator, MissingRequiredMemoryError
from models import AgentStateUpdate

def test_temp():
    validator = WorkflowValidator("sample_workflow.yaml")
    scheduler = SchedulerEngine(workflow_validator=validator)
    main_agent = MainAgent(scheduler, default_save_path="/workspace")
    
    scheduler.workflow_state.current_stage = "plan"
    scheduler.start()
    
    import unittest.mock as mock
    with mock.patch.object(main_agent, '_generate_state_update') as mock_update:
        mock_update.return_value = AgentStateUpdate(
            action="plan_finished",
            next_stage="draft",
            updates_to_memory={"topic": "AI"}
        )
        try:
            main_agent.wakeup("start planning", [])
            print("No exception thrown")
        except MissingRequiredMemoryError as e:
            print("Caught expected exception:", e)

test_temp()

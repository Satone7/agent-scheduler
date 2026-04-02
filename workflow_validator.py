import yaml
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class WorkflowState:
    """当前工作流的状态"""
    current_phase: str
    memory: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentStateUpdate:
    """Agent 提交的状态更新"""
    target_phase: str
    updates_to_memory: Dict[str, Any] = field(default_factory=dict)

class WorkflowValidatorError(Exception):
    """工作流校验异常基类"""
    pass

class PhaseNotFoundError(WorkflowValidatorError):
    """阶段未找到异常"""
    pass

class MissingRequiredMemoryError(WorkflowValidatorError):
    """缺少必填字段异常"""
    pass

class InvalidTransitionError(WorkflowValidatorError):
    """非法流转异常"""
    pass

class WorkflowValidator:
    """工作流校验器，加载 YAML 配置并校验状态更新"""
    
    def __init__(self, yaml_path: str):
        self.yaml_path = yaml_path
        self.workflow_def = self._load_yaml(yaml_path)
        self.phases = self.workflow_def.get("phases", {})
        
    def _load_yaml(self, path: str) -> Dict[str, Any]:
        """加载 YAML 配置文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise WorkflowValidatorError(f"Failed to load workflow definition from {path}: {str(e)}")

    def validate(self, current_state: WorkflowState, update: AgentStateUpdate) -> bool:
        """
        校验状态流转是否合法。
        
        Args:
            current_state: 当前工作流状态
            update: Agent 提交的状态更新
            
        Returns:
            bool: 校验通过返回 True
            
        Raises:
            PhaseNotFoundError: 目标阶段在 YAML 中不存在
            InvalidTransitionError: 当前阶段不允许流转到目标阶段
            MissingRequiredMemoryError: updates_to_memory 中未提供必填字段
        """
        target_phase = update.target_phase
        
        # 1. 检查目标阶段是否存在于 YAML 定义中
        if target_phase not in self.phases:
            raise PhaseNotFoundError(f"目标阶段 '{target_phase}' 在工作流定义中不存在。")
            
        # 2. 检查状态流转是否合法（当前阶段 -> 目标阶段）
        current_phase = current_state.current_phase
        if current_phase:
            if current_phase not in self.phases:
                raise PhaseNotFoundError(f"当前阶段 '{current_phase}' 在工作流定义中不存在。")
            
            # 如果当前阶段定义了 next_phases，并且它不是空列表，则校验目标阶段是否在允许列表中
            # （如果 next_phases 为空或未定义，这里假设允许流转，具体取决于业务逻辑。这里我们严格限制必须在列表中，除非列表为 None）
            allowed_next_phases = self.phases[current_phase].get("next_phases")
            if allowed_next_phases is not None and target_phase not in allowed_next_phases:
                raise InvalidTransitionError(
                    f"不允许从阶段 '{current_phase}' 流转到 '{target_phase}'。"
                    f"允许的下一阶段有: {allowed_next_phases}"
                )

        # 3. 检查必填字段是否在 updates_to_memory（或当前 memory）中被提供
        target_phase_def = self.phases[target_phase]
        required_memory = target_phase_def.get("required_memory", [])
        
        missing_fields = []
        for field_name in required_memory:
            # 字段需要由 update 提供，或者已经存在于当前的 memory 中
            if field_name not in update.updates_to_memory and field_name not in current_state.memory:
                missing_fields.append(field_name)
                
        if missing_fields:
            raise MissingRequiredMemoryError(
                f"流转到阶段 '{target_phase}' 缺少必填字段: {missing_fields}"
            )
            
        return True

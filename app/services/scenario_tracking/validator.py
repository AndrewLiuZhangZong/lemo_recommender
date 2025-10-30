"""
场景埋点数据验证器

职责：
1. 根据场景配置验证埋点数据
2. 检查必填字段
3. 验证字段类型和范围
4. 提供详细的错误信息
"""

from typing import Dict, Any, List, Optional
import re
import logging

from app.models.scenario_tracking import (
    ScenarioTrackingConfig,
    FieldValidation,
    FieldType,
    TrackingValidationResult
)

logger = logging.getLogger(__name__)


class TrackingDataValidator:
    """场景埋点数据验证器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化验证器
        
        Args:
            config: 场景埋点配置（可选）
        """
        self.config = config
        self.required_fields = []
        self.optional_fields = []
        
        if config:
            self.required_fields = config.get("required_fields", [])
            self.optional_fields = config.get("optional_fields", [])
    
    def validate(
        self,
        scenario_data: Dict[str, Any],
        strict: bool = False
    ) -> TrackingValidationResult:
        """
        验证场景数据
        
        Args:
            scenario_data: 场景特定数据
            strict: 是否严格模式（严格模式下，未定义的字段也会报错）
        
        Returns:
            TrackingValidationResult: 验证结果
        """
        errors = []
        warnings = []
        missing_fields = []
        invalid_fields = {}
        
        # 如果没有配置，跳过验证（允许所有数据）
        if not self.config:
            return TrackingValidationResult(
                is_valid=True,
                errors=[],
                warnings=["No tracking config found, validation skipped"],
                missing_fields=[],
                invalid_fields={}
            )
        
        # 1. 检查必填字段
        for field_def in self.required_fields:
            field_name = field_def.get("field_name")
            
            if field_name not in scenario_data:
                missing_fields.append(field_name)
                errors.append(
                    f"Required field '{field_name}' is missing"
                )
            else:
                # 验证字段值
                error = self._validate_field_value(
                    field_name,
                    scenario_data[field_name],
                    field_def
                )
                if error:
                    invalid_fields[field_name] = error
                    errors.append(error)
        
        # 2. 验证可选字段（如果提供了）
        for field_def in self.optional_fields:
            field_name = field_def.get("field_name")
            
            if field_name in scenario_data:
                error = self._validate_field_value(
                    field_name,
                    scenario_data[field_name],
                    field_def
                )
                if error:
                    invalid_fields[field_name] = error
                    errors.append(error)
        
        # 3. 严格模式：检查未定义的字段
        if strict:
            defined_fields = set(
                [f.get("field_name") for f in self.required_fields] +
                [f.get("field_name") for f in self.optional_fields]
            )
            
            for field_name in scenario_data.keys():
                if field_name not in defined_fields:
                    warnings.append(
                        f"Undefined field '{field_name}' (not in config)"
                    )
        
        # 判断是否验证通过
        is_valid = len(errors) == 0 and len(missing_fields) == 0
        
        return TrackingValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            missing_fields=missing_fields,
            invalid_fields=invalid_fields
        )
    
    def _validate_field_value(
        self,
        field_name: str,
        value: Any,
        field_def: Dict[str, Any]
    ) -> Optional[str]:
        """
        验证单个字段的值
        
        Args:
            field_name: 字段名
            value: 字段值
            field_def: 字段定义
        
        Returns:
            错误信息，验证通过返回None
        """
        field_type = field_def.get("field_type")
        
        # 空值检查
        if value is None:
            if field_def.get("required", False):
                return f"Field '{field_name}' is required but got None"
            return None
        
        # 类型验证
        type_error = self._validate_type(field_name, value, field_type)
        if type_error:
            return type_error
        
        # 数值范围验证
        if field_type in [FieldType.INTEGER, FieldType.FLOAT]:
            range_error = self._validate_numeric_range(
                field_name, value, field_def
            )
            if range_error:
                return range_error
        
        # 字符串验证
        if field_type == FieldType.STRING:
            string_error = self._validate_string(
                field_name, value, field_def
            )
            if string_error:
                return string_error
        
        # 枚举值验证
        enum_values = field_def.get("enum_values")
        if enum_values:
            enum_error = self._validate_enum(
                field_name, value, enum_values
            )
            if enum_error:
                return enum_error
        
        return None
    
    def _validate_type(
        self,
        field_name: str,
        value: Any,
        field_type: str
    ) -> Optional[str]:
        """验证字段类型"""
        
        if field_type == FieldType.STRING:
            if not isinstance(value, str):
                return f"Field '{field_name}' must be string, got {type(value).__name__}"
        
        elif field_type == FieldType.INTEGER:
            if not isinstance(value, int) or isinstance(value, bool):
                return f"Field '{field_name}' must be integer, got {type(value).__name__}"
        
        elif field_type == FieldType.FLOAT:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return f"Field '{field_name}' must be float, got {type(value).__name__}"
        
        elif field_type == FieldType.BOOLEAN:
            if not isinstance(value, bool):
                return f"Field '{field_name}' must be boolean, got {type(value).__name__}"
        
        elif field_type == FieldType.TIMESTAMP:
            if not isinstance(value, int):
                return f"Field '{field_name}' must be timestamp (integer), got {type(value).__name__}"
        
        elif field_type == FieldType.ARRAY_STRING:
            if not isinstance(value, list):
                return f"Field '{field_name}' must be array, got {type(value).__name__}"
            for i, item in enumerate(value):
                if not isinstance(item, str):
                    return f"Field '{field_name}[{i}]' must be string, got {type(item).__name__}"
        
        elif field_type == FieldType.ARRAY_INTEGER:
            if not isinstance(value, list):
                return f"Field '{field_name}' must be array, got {type(value).__name__}"
            for i, item in enumerate(value):
                if not isinstance(item, int) or isinstance(item, bool):
                    return f"Field '{field_name}[{i}]' must be integer, got {type(item).__name__}"
        
        elif field_type == FieldType.JSON:
            if not isinstance(value, (dict, list)):
                return f"Field '{field_name}' must be JSON (dict or list), got {type(value).__name__}"
        
        return None
    
    def _validate_numeric_range(
        self,
        field_name: str,
        value: float,
        field_def: Dict[str, Any]
    ) -> Optional[str]:
        """验证数值范围"""
        
        min_value = field_def.get("min_value")
        max_value = field_def.get("max_value")
        
        if min_value is not None and value < min_value:
            return f"Field '{field_name}' value {value} is less than min {min_value}"
        
        if max_value is not None and value > max_value:
            return f"Field '{field_name}' value {value} is greater than max {max_value}"
        
        return None
    
    def _validate_string(
        self,
        field_name: str,
        value: str,
        field_def: Dict[str, Any]
    ) -> Optional[str]:
        """验证字符串"""
        
        min_length = field_def.get("min_length")
        max_length = field_def.get("max_length")
        pattern = field_def.get("pattern")
        
        if min_length is not None and len(value) < min_length:
            return f"Field '{field_name}' length {len(value)} is less than min {min_length}"
        
        if max_length is not None and len(value) > max_length:
            return f"Field '{field_name}' length {len(value)} is greater than max {max_length}"
        
        if pattern:
            try:
                if not re.match(pattern, value):
                    return f"Field '{field_name}' value '{value}' does not match pattern '{pattern}'"
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")
        
        return None
    
    def _validate_enum(
        self,
        field_name: str,
        value: Any,
        enum_values: List[str]
    ) -> Optional[str]:
        """验证枚举值"""
        
        # 转换为字符串比较
        value_str = str(value)
        enum_values_str = [str(v) for v in enum_values]
        
        if value_str not in enum_values_str:
            return (
                f"Field '{field_name}' value '{value}' is not in "
                f"allowed values {enum_values}"
            )
        
        return None
    
    def validate_action_type(
        self,
        action_type: str
    ) -> bool:
        """
        验证行为类型是否推荐
        
        Args:
            action_type: 行为类型
        
        Returns:
            是否推荐（如果没有配置，返回True）
        """
        if not self.config:
            return True
        
        recommended_actions = self.config.get("recommended_actions", [])
        
        if not recommended_actions:
            return True
        
        return action_type in recommended_actions


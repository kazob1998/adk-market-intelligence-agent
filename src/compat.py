"""
Compatibility layer for Pydantic and environment utilities.
Uses real Pydantic v2 when installed, with graceful fallback for zero-dependency environments.
"""

from typing import Any, Dict, List, Optional
import json

try:
    from pydantic import BaseModel, Field, ValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

    class ValidationError(ValueError):
        def __init__(self, errors: Optional[List[Dict[str, Any]]] = None, msg: str = "Validation failed"):
            super().__init__(msg)
            self._errors = errors or [{"msg": msg}]

        def errors(self) -> List[Dict[str, Any]]:
            return self._errors

    class FieldInfo:
        def __init__(
            self,
            default: Any = ...,
            default_factory: Any = None,
            description: str = "",
            ge: Any = None,
            le: Any = None,
            min_length: Any = None,
            max_length: Any = None
        ):
            self.default = default
            self.default_factory = default_factory
            self.description = description
            self.ge = ge
            self.le = le
            self.min_length = min_length
            self.max_length = max_length

    def Field(
        default: Any = ...,
        default_factory: Any = None,
        description: str = "",
        ge: Any = None,
        le: Any = None,
        min_length: Any = None,
        max_length: Any = None
    ) -> Any:
        return FieldInfo(
            default=default,
            default_factory=default_factory,
            description=description,
            ge=ge,
            le=le,
            min_length=min_length,
            max_length=max_length
        )

    class BaseModel:
        def __init__(self, **data):
            cls = self.__class__
            errors = []

            # Collect annotations from class and all base classes
            annotations = {}
            for base in reversed(cls.__mro__):
                annotations.update(getattr(base, "__annotations__", {}))

            for field_name in annotations:
                field_val = data.get(field_name)
                has_class_attr = hasattr(cls, field_name)
                class_attr = getattr(cls, field_name, None) if has_class_attr else None

                if field_val is not None:
                    # Constraint checking
                    if isinstance(class_attr, FieldInfo):
                        if class_attr.min_length is not None and isinstance(field_val, (str, list)) and len(field_val) < class_attr.min_length:
                            errors.append({"loc": [field_name], "msg": f"String/list too short (min {class_attr.min_length})"})
                        if class_attr.max_length is not None and isinstance(field_val, (str, list)) and len(field_val) > class_attr.max_length:
                            errors.append({"loc": [field_name], "msg": f"String/list too long (max {class_attr.max_length})"})
                        if class_attr.ge is not None and isinstance(field_val, (int, float)) and field_val < class_attr.ge:
                            errors.append({"loc": [field_name], "msg": f"Value too small (ge {class_attr.ge})"})
                        if class_attr.le is not None and isinstance(field_val, (int, float)) and field_val > class_attr.le:
                            errors.append({"loc": [field_name], "msg": f"Value too large (le {class_attr.le})"})
                    setattr(self, field_name, field_val)
                elif isinstance(class_attr, FieldInfo):
                    if class_attr.default_factory is not None:
                        setattr(self, field_name, class_attr.default_factory())
                    elif class_attr.default is not ...:
                        setattr(self, field_name, class_attr.default)
                    else:
                        errors.append({"loc": [field_name], "msg": "Field required"})
                elif has_class_attr:
                    setattr(self, field_name, class_attr)
                else:
                    errors.append({"loc": [field_name], "msg": "Field required"})

            for k, v in data.items():
                if not hasattr(self, k):
                    setattr(self, k, v)

            if errors:
                raise ValidationError(errors=errors)

        def model_dump(self) -> Dict[str, Any]:
            result = {}
            for k, v in self.__dict__.items():
                if isinstance(v, BaseModel):
                    result[k] = v.model_dump()
                elif isinstance(v, list):
                    result[k] = [item.model_dump() if isinstance(item, BaseModel) else item for item in v]
                elif isinstance(v, dict):
                    result[k] = {dk: (dv.model_dump() if isinstance(dv, BaseModel) else dv) for dk, dv in v.items()}
                else:
                    result[k] = v
            return result

        def model_dump_json(self) -> str:
            return json.dumps(self.model_dump())

        @classmethod
        def model_validate(cls, obj: Any):
            if isinstance(obj, cls):
                return obj
            if isinstance(obj, dict):
                return cls(**obj)
            raise ValidationError(msg=f"Cannot validate {type(obj)} into {cls.__name__}")


__all__ = ["BaseModel", "Field", "ValidationError", "PYDANTIC_AVAILABLE"]

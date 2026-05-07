"""Helpers for converting Pydantic models into compact prompt schemas.

The goal is to keep Pydantic schemas as the single source of truth while giving
LLMs a short, readable JSON-like schema in prompts.
"""

from __future__ import annotations

from types import UnionType
from typing import Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel


def model_to_prompt_schema(model: type[BaseModel]) -> str:
    """Convert a Pydantic model into a compact JSON-like schema string.

    Example output:
    {
      "topic_mismatch": boolean,
      "situation_mismatch": boolean,
      "explanation": "string",
      "positive_feedback": ["string"],
      "improvement_feedback": ["string"]
    }
    """
    return _model_to_schema_block(model, indent=0)


def _model_to_schema_block(model: type[BaseModel], indent: int) -> str:
    spaces = " " * indent
    inner_spaces = " " * (indent + 2)

    lines = [f"{spaces}{{"]

    fields = list(model.model_fields.items())

    for index, (field_name, field_info) in enumerate(fields):
        comma = "," if index < len(fields) - 1 else ""
        type_repr = _type_to_prompt_type(field_info.annotation, indent + 2)
        lines.append(f'{inner_spaces}"{field_name}": {type_repr}{comma}')

    lines.append(f"{spaces}}}")
    return "\n".join(lines)


def _type_to_prompt_type(annotation: Any, indent: int) -> str:
    origin = get_origin(annotation)
    args = get_args(annotation)

    if annotation is str:
        return '"string"'

    if annotation is int:
        return "integer"

    if annotation is float:
        return "number"

    if annotation is bool:
        return "boolean"

    if origin is list:
        item_annotation = args[0] if args else str
        item_type = _type_to_prompt_type(item_annotation, indent)
        return f"[{item_type}]"

    if origin is Literal:
        literal_values = " | ".join(_format_literal_value(arg) for arg in args)
        return f'"{literal_values}"'

    if origin in (Union, UnionType):
        has_none = any(arg is type(None) for arg in args)
        non_none_args = [arg for arg in args if arg is not type(None)]

        union_parts = [_type_to_prompt_type(arg, indent) for arg in non_none_args]
        if has_none:
            union_parts.append("null")

        return " | ".join(union_parts)

    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return _model_to_schema_block(annotation, indent)

    return '"string"'


def _format_literal_value(value: Any) -> str:
    if isinstance(value, str):
        return value

    return str(value)
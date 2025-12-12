import json
from typing import Any, Dict


def _toml_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        # безопасное экранирование как JSON-строка (совместимо с TOML basic string)
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ", ".join(_toml_value(x) for x in v) + "]"
    raise TypeError(f"Unsupported value type: {type(v)}")


def to_toml(env: Dict[str, Any]) -> str:
    # простой плоский TOML: KEY = value
    lines = []
    for k in sorted(env.keys()):
        lines.append(f"{k} = {_toml_value(env[k])}")
    return "\n".join(lines) + "\n"

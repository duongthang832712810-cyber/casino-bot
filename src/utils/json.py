from __future__ import annotations

import json as _json
from typing import Any


def dumps(value: Any) -> str:
    return _json.dumps(value, ensure_ascii=False)


def loads(value: str) -> Any:
    return _json.loads(value)

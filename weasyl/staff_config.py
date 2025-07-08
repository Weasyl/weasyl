import ast
from typing import Any

from libweasyl.staff import StaffConfig
from weasyl import macro


def _is_id(value: Any) -> bool:
    return type(value) is int and 0 < value <= 0x7fff_ffff


def load() -> StaffConfig:
    """
    Load staff from a Python config file at `macro.MACRO_SYS_STAFF_CONFIG_PATH`.
    """
    with open(macro.MACRO_SYS_STAFF_CONFIG_PATH) as f:
        source = f.read()

    module = ast.parse(source)
    staff = {}

    for statement in module.body:
        if not isinstance(statement, ast.Assign):
            raise SyntaxError("Unexpected node in staff configuration")

        target = statement.targets[0]

        if len(statement.targets) != 1 or not isinstance(target, ast.Name):
            raise SyntaxError("Unexpected assignment target in staff configuration")

        if target.id not in {"directors", "admins", "mods", "developers", "wesley"}:
            raise SyntaxError("Unexpected key in staff configuration: %r" % (target.id,))

        if target.id in staff:
            raise SyntaxError(f"Key specified multiple times in staff configuration: {target.id}")

        value = ast.literal_eval(statement.value)

        if target.id == "wesley":
            if not (value is None or _is_id(value)):
                raise SyntaxError(f"Unexpected value for {target.id} in staff configuration (expected id or None): {value!r}")
        elif not (isinstance(value, list) and all(map(_is_id, value))):
            raise SyntaxError(f"Unexpected value for {target.id} in staff configuration (expected list of ids): {value!r}")

        staff[target.id] = value

    return StaffConfig(**staff)

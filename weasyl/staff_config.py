"""
Retrieve a dictionary of Weasyl staff.
"""

import ast

from weasyl import macro


def load():
    """
    Load staff from a Python config file.

    Parameters: None. Path is obtained from `macro.MACRO_SYS_STAFF_CONFIG_PATH`

    Returns:
        staff_dict: A dictionary with the staff member user IDs.
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

        # Techs no longer exist as a role, but still allow technical_staff
        # to prevent an outage when upgrading past its removal.

        if target.id not in {"directors", "technical_staff", "admins", "mods", "developers", "wesley"}:
            raise SyntaxError("Unexpected key in staff configuration: %r" % (target.id,))

        if target.id != "technical_staff":
            staff[target.id] = ast.literal_eval(statement.value)

    return staff

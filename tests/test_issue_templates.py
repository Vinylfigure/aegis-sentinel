"""Structural checks for GitHub issue forms under .github/ISSUE_TEMPLATE/.

These run inside `verify.sh full`, which is both what CI runs and what a
dispatched agent is allowed to run — so a malformed template fails the same
way for a human and for a child agent. The work order that introduced the
work-order form could not verify itself: it asked for a YAML parse when no
allowlisted command could perform one. This file is that check, relocated
somewhere both actors can reach.
"""

from pathlib import Path

import pytest
import yaml

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / ".github" / "ISSUE_TEMPLATE"

# The four fields a work order must carry, ported from the /plan-feature skill.
WORK_ORDER_FIELDS = {"objective", "done-means", "allowed-paths", "effort-budget"}


def template_files():
    return sorted(p for p in TEMPLATE_DIR.glob("*.y*ml") if p.name != "config.yml")


def test_template_dir_is_not_empty():
    assert template_files(), f"no issue forms found in {TEMPLATE_DIR}"


@pytest.mark.parametrize("path", template_files(), ids=lambda p: p.name)
def test_template_parses_and_has_required_shape(path):
    form = yaml.safe_load(path.read_text())

    assert isinstance(form, dict), f"{path.name}: top level must be a mapping"
    for key in ("name", "description", "body"):
        assert form.get(key), f"{path.name}: missing required key {key!r}"
    assert isinstance(form["body"], list), f"{path.name}: body must be a list"

    for element in form["body"]:
        assert "type" in element, f"{path.name}: every body element needs a type"
        # markdown blocks are display-only and carry no id.
        if element["type"] != "markdown":
            assert element.get("id"), f"{path.name}: input elements need an id"
            assert element.get("attributes", {}).get("label"), (
                f"{path.name}: {element.get('id')} needs a label"
            )


def test_work_order_template_carries_all_four_fields():
    path = TEMPLATE_DIR / "work-order.yml"
    assert path.exists(), "the work-order template is missing"

    form = yaml.safe_load(path.read_text())
    ids = {e.get("id") for e in form["body"] if e.get("id")}

    missing = WORK_ORDER_FIELDS - ids
    assert not missing, f"work-order.yml is missing field(s): {sorted(missing)}"

    # A field a filer can skip is a field that will be skipped — the whole
    # point of porting the shape is that scope is not optional.
    not_required = sorted(
        e["id"]
        for e in form["body"]
        if e.get("id") in WORK_ORDER_FIELDS and not e.get("validations", {}).get("required")
    )
    assert not not_required, f"work-order.yml fields must be required: {not_required}"

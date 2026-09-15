#!/usr/bin/env python3
# Purpose: Test explicit keep-data and approved delete-data uninstall choices.

from __future__ import annotations

import pytest

from expertiseos.ownership import (
    DeletionPlan,
    KnowledgeRef,
    OwnershipError,
    UninstallDataChoice,
    plan_uninstall,
)


def test_keep_data_uninstall_has_no_deletion_plan() -> None:
    plan = plan_uninstall(UninstallDataChoice.KEEP, None)
    assert plan.remove_host_integrations
    assert plan.unregister_service
    assert plan.deletion_plan is None


def test_delete_data_uninstall_requires_approved_plan() -> None:
    with pytest.raises(OwnershipError, match="requires"):
        plan_uninstall(UninstallDataChoice.DELETE, None)
    deletion = DeletionPlan("delete-1", (KnowledgeRef("knowledge-1", 1),), True, True, True, ())
    assert plan_uninstall(UninstallDataChoice.DELETE, deletion).deletion_plan == deletion

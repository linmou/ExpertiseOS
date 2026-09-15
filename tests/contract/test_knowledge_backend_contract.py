#!/usr/bin/env python3
# Purpose: Test src/expertiseos/knowledge/backend.py C003 retrieval contract values.

from dataclasses import MISSING, fields

import pytest

from expertiseos.knowledge.backend import (
    BackendContractError,
    RetrievalResponse,
    SearchQuery,
    SearchResult,
)


def test_c003_contract_dataclasses_require_every_field() -> None:
    for data_type in (SearchQuery, SearchResult, RetrievalResponse):
        assert all(field.default is MISSING for field in fields(data_type))
        assert all(field.default_factory is MISSING for field in fields(data_type))


@pytest.mark.parametrize("limit", [0, -1, 21])
def test_search_limit_must_be_between_one_and_twenty(limit: int) -> None:
    with pytest.raises(BackendContractError, match="limit"):
        SearchQuery("query", limit, None, (), (), ())


def test_search_query_rejects_blank_text() -> None:
    with pytest.raises(BackendContractError, match="text"):
        SearchQuery("", 1, None, (), (), ())

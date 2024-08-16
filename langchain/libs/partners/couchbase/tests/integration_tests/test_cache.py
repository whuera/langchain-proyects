"""Test Couchbase Cache functionality"""

import os
from datetime import timedelta
from typing import Any

import pytest
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from langchain_core.globals import get_llm_cache, set_llm_cache
from langchain_core.outputs import Generation

from langchain_couchbase.cache import CouchbaseCache, CouchbaseSemanticCache
from tests.utils import FakeEmbeddings, FakeLLM

CONNECTION_STRING = os.getenv("COUCHBASE_CONNECTION_STRING", "")
BUCKET_NAME = os.getenv("COUCHBASE_BUCKET_NAME", "")
SCOPE_NAME = os.getenv("COUCHBASE_SCOPE_NAME", "")
CACHE_COLLECTION_NAME = os.getenv("COUCHBASE_CACHE_COLLECTION_NAME", "")
SEMANTIC_CACHE_COLLECTION_NAME = os.getenv(
    "COUCHBASE_SEMANTIC_CACHE_COLLECTION_NAME", ""
)
USERNAME = os.getenv("COUCHBASE_USERNAME", "")
PASSWORD = os.getenv("COUCHBASE_PASSWORD", "")
INDEX_NAME = os.getenv("COUCHBASE_SEMANTIC_CACHE_INDEX_NAME", "")


def set_all_env_vars() -> bool:
    """Check if all environment variables are set"""
    return all(
        [
            CONNECTION_STRING,
            BUCKET_NAME,
            SCOPE_NAME,
            CACHE_COLLECTION_NAME,
            USERNAME,
            PASSWORD,
            INDEX_NAME,
        ]
    )


def get_cluster() -> Any:
    """Get a couchbase cluster object"""
    auth = PasswordAuthenticator(USERNAME, PASSWORD)
    options = ClusterOptions(auth)
    connect_string = CONNECTION_STRING
    cluster = Cluster(connect_string, options)

    # Wait until the cluster is ready for use.
    cluster.wait_until_ready(timedelta(seconds=5))

    return cluster


@pytest.fixture()
def cluster() -> Any:
    """Get a couchbase cluster object"""
    return get_cluster()


@pytest.mark.skipif(
    not set_all_env_vars(), reason="Missing Couchbase environment variables"
)
class TestCouchbaseCache:
    def test_cache(self, cluster: Any) -> None:
        """Test standard LLM cache functionality"""
        set_llm_cache(
            CouchbaseCache(
                cluster=cluster,
                bucket_name=BUCKET_NAME,
                scope_name=SCOPE_NAME,
                collection_name=CACHE_COLLECTION_NAME,
            )
        )

        llm = FakeLLM()

        params = llm.dict()
        params["stop"] = None
        llm_string = str(sorted([(k, v) for k, v in params.items()]))
        get_llm_cache().update("foo", llm_string, [Generation(text="fizz")])
        cache_output = get_llm_cache().lookup("foo", llm_string)
        assert cache_output == [Generation(text="fizz")]

        get_llm_cache().clear()
        output = get_llm_cache().lookup("bar", llm_string)
        assert output != [Generation(text="fizz")]

    def test_semantic_cache(self, cluster: Any) -> None:
        """Test semantic LLM cache functionality"""
        set_llm_cache(
            CouchbaseSemanticCache(
                cluster=cluster,
                embedding=FakeEmbeddings(),
                index_name=INDEX_NAME,
                bucket_name=BUCKET_NAME,
                scope_name=SCOPE_NAME,
                collection_name=SEMANTIC_CACHE_COLLECTION_NAME,
            )
        )

        llm = FakeLLM()

        params = llm.dict()
        params["stop"] = None
        llm_string = str(sorted([(k, v) for k, v in params.items()]))
        get_llm_cache().update(
            "foo", llm_string, [Generation(text="fizz"), Generation(text="Buzz")]
        )

        # foo and bar will have the same embedding produced by FakeEmbeddings
        cache_output = get_llm_cache().lookup("bar", llm_string)
        assert cache_output == [Generation(text="fizz"), Generation(text="Buzz")]

        # clear the cache
        get_llm_cache().clear()
        output = get_llm_cache().lookup("bar", llm_string)
        assert output != [Generation(text="fizz"), Generation(text="Buzz")]

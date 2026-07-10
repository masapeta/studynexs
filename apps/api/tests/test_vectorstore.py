"""Vector store — nearest-neighbour retrieval, and the sacred rule extended into RAG:
retrieval is hard-scoped by school_id (no cross-tenant leakage). In-memory unit tests plus a
Qdrant integration test (skipped if Qdrant is unreachable)."""

import socket

import pytest

from app.core.config import get_settings
from app.modules.ai.vectorstore import VectorPoint, collection_name
from app.modules.ai.vectorstore.memory_store import InMemoryVectorStore
from app.modules.ai.vectorstore.qdrant_store import QdrantVectorStore

DIM = 4


def _pt(pid: str, vec: list[float], school: str, **extra) -> VectorPoint:
    return VectorPoint(id=pid, vector=vec, payload={"school_id": school, **extra})


@pytest.mark.asyncio
async def test_memory_search_and_tenant_isolation():
    store = InMemoryVectorStore()
    await store.ensure_collection("c", dimensions=DIM)
    await store.upsert(
        "c",
        [
            _pt("a", [1, 0, 0, 0], "schoolA", text="alpha"),
            _pt("b", [0, 1, 0, 0], "schoolA", text="beta"),
            _pt("x", [1, 0, 0, 0], "schoolB", text="other-tenant"),
        ],
    )
    res = await store.search("c", [1, 0, 0, 0], school_id="schoolA", top_k=5)
    ids = [m.id for m in res]
    assert ids[0] == "a"  # nearest for schoolA
    assert "x" not in ids  # schoolB's identical vector is NEVER returned to schoolA
    resb = await store.search("c", [1, 0, 0, 0], school_id="schoolB", top_k=5)
    assert [m.id for m in resb] == ["x"]


@pytest.mark.asyncio
async def test_memory_extra_filter_pack_scope():
    store = InMemoryVectorStore()
    await store.ensure_collection("c", dimensions=DIM)
    await store.upsert(
        "c",
        [
            _pt("p1", [1, 0, 0, 0], "s", pack_id="P1"),
            _pt("p2", [1, 0, 0, 0], "s", pack_id="P2"),
        ],
    )
    res = await store.search("c", [1, 0, 0, 0], school_id="s", filters={"pack_id": "P1"})
    assert [m.id for m in res] == ["p1"]


@pytest.mark.asyncio
async def test_memory_requires_school_id_in_payload():
    store = InMemoryVectorStore()
    with pytest.raises(ValueError):
        await store.upsert(
            "c", [VectorPoint(id="x", vector=[1, 0, 0, 0], payload={"t": "no tenant"})]
        )


@pytest.mark.asyncio
async def test_memory_delete_is_tenant_scoped():
    store = InMemoryVectorStore()
    await store.ensure_collection("c", dimensions=DIM)
    await store.upsert("c", [_pt("a", [1, 0, 0, 0], "s"), _pt("b", [0, 1, 0, 0], "s2")])
    await store.delete("c", school_id="s")
    assert await store.search("c", [1, 0, 0, 0], school_id="s") == []
    assert len(await store.search("c", [0, 1, 0, 0], school_id="s2")) == 1


def test_collection_name_encodes_provider_and_dim():
    assert collection_name("Curriculum", "OpenAI", 1536) == "curriculum__openai__1536"


def _qdrant_reachable() -> bool:
    s = get_settings()
    try:
        with socket.create_connection((s.QDRANT_HOST, s.QDRANT_PORT), timeout=1):
            return True
    except OSError:
        return False


@pytest.mark.asyncio
@pytest.mark.skipif(not _qdrant_reachable(), reason="Qdrant not reachable")
async def test_qdrant_search_missing_collection_is_empty_not_404():
    """First-ever retrieval for a namespace (collection not yet created) returns [], not a 404."""
    store = QdrantVectorStore()
    coll = "studynexs_pytest_missing_collection"
    client = store._get_client()
    if await client.collection_exists(coll):
        await client.delete_collection(coll)
    assert await store.search(coll, [1, 0, 0, 0], school_id="schoolA", top_k=5) == []
    # delete on a missing collection is a safe no-op
    await store.delete(coll, school_id="schoolA")


@pytest.mark.asyncio
@pytest.mark.skipif(not _qdrant_reachable(), reason="Qdrant not reachable")
async def test_qdrant_roundtrip_and_tenant_isolation():
    store = QdrantVectorStore()
    coll = "studynexs_pytest_vectors"
    client = store._get_client()
    if await client.collection_exists(coll):
        await client.delete_collection(coll)
    await store.ensure_collection(coll, dimensions=DIM)
    try:
        await store.upsert(
            coll,
            [
                _pt("11111111-1111-1111-1111-111111111111", [1, 0, 0, 0], "schoolA", text="a"),
                _pt("22222222-2222-2222-2222-222222222222", [1, 0, 0, 0], "schoolB", text="b"),
            ],
        )
        res = await store.search(coll, [1, 0, 0, 0], school_id="schoolA", top_k=5)
        ids = [m.id for m in res]
        assert "11111111-1111-1111-1111-111111111111" in ids
        # schoolB's identical vector must NOT leak to schoolA (tenant filter in Qdrant)
        assert "22222222-2222-2222-2222-222222222222" not in ids
    finally:
        await client.delete_collection(coll)

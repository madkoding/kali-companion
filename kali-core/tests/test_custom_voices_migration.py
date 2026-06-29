"""Tests for custom voices DB migration from qwen3-voicedesign to qwen3."""

import asyncio
import tempfile
import os
from kali_core.nest.store import SessionStore


def test_custom_voices_migration_qwen3_voicedesign_to_qwen3():
    db_path = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
    store = SessionStore(db_path)

    async def setup_and_migrate():
        import aiosqlite
        await store._ensure_db()
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "INSERT INTO custom_voices (id, name, provider, instructions, seed, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("cv_legacy1", "Test", "qwen3-voicedesign", "test instructions", 42, "2025-01-01", "2025-01-01"),
            )
            await db.commit()
        store2 = SessionStore(db_path)
        await store2._ensure_db()
        voices = await store2.list_custom_voices(provider="qwen3")
        assert len(voices) == 1
        assert voices[0]["provider"] == "qwen3"
        assert voices[0]["id"] == "cv_legacy1"

    asyncio.run(setup_and_migrate())
    os.unlink(db_path)


def test_custom_voices_default_is_qwen3():
    db_path = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
    store = SessionStore(db_path)

    async def create_and_check():
        import aiosqlite
        await store._ensure_db()
        voice = await store.create_custom_voice(name="Test", provider="qwen3", instructions="test", seed=42)
        assert voice["provider"] == "qwen3"
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("SELECT provider FROM custom_voices WHERE id = ?", (voice["id"],))
            row = await cursor.fetchone()
            assert row[0] == "qwen3"

    asyncio.run(create_and_check())
    os.unlink(db_path)
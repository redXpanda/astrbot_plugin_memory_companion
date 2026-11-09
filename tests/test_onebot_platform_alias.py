from __future__ import annotations

from dataclasses import replace

import pytest
from core.injection import MEMORY_COMPANION_INJECTION_HEADER
from core.memory_revision import memory_ref

from .test_memory_correction import context, record
from .test_reply_continuity import body, publish
from .test_reply_continuity import service as service


@pytest.mark.parametrize(
    ("memory_platform", "request_platform", "same_bot", "expected"),
    [
        ("astrbot_onebot", "aiocqhttp", True, True),
        ("aiocqhttp", "astrbot_onebot", True, True),
        ("astrbot_onebot", "telegram", True, False),
        ("astrbot_onebot", "aiocqhttp", False, False),
    ],
)
@pytest.mark.asyncio
async def test_reply_validation_normalizes_onebot_alias_without_crossing_boundaries(
    service,
    memory_platform,
    request_platform,
    same_bot,
    expected,
):
    ctx = context(
        platform=request_platform, session_id="astrbot_onebot:FriendMessage:user"
    )
    item = record(
        platform=memory_platform,
        session_id=ctx.session_id,
        message_id="source-message",
        confidence=0.95,
        importance=0.8,
    )
    await service.store.insert_memory(item)
    item = await service.store.get_memory(item.id)
    if not same_bot:
        ctx = replace(ctx, bot_id="another-bot")

    ok, req, event = await publish(service, item, ctx=ctx)

    assert ok is expected
    if expected:
        assert item.content in body(req)
        assert event.memory_companion_injection_state["memory_refs"] == [
            memory_ref(item)
        ]
    else:
        assert MEMORY_COMPANION_INJECTION_HEADER not in body(req)

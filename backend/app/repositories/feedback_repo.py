from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import Feedback


class FeedbackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, attempt_id: uuid.UUID, content: dict) -> Feedback:
        feedback = Feedback(attempt_id=attempt_id, content=content)
        self._session.add(feedback)
        await self._session.flush()
        return feedback

    async def get(self, attempt_id: uuid.UUID) -> Feedback | None:
        stmt = (
            select(Feedback)
            .where(Feedback.attempt_id == attempt_id)
            .order_by(Feedback.created_at.desc())
            .limit(1)
        )
        return await self._session.scalar(stmt)

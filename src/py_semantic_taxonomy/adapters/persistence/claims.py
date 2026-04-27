from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, insert, select, update

from py_semantic_taxonomy.adapters.persistence.database import create_engine
from py_semantic_taxonomy.adapters.persistence.tables import contributor_claim_table


class ContributorClaimStore:
    async def create(
        self,
        *,
        kind: str,
        title: str,
        target_iri: str | None,
        payload: dict[str, Any],
        submitted_by: dict[str, Any],
    ) -> int:
        stmt = insert(contributor_claim_table).values(
            kind=kind,
            status="pending",
            title=title,
            target_iri=target_iri or None,
            payload=payload,
            submitted_by=submitted_by,
            review={},
            created_at=datetime.now(tz=timezone.utc),
        )
        async with create_engine().begin() as conn:
            result = await conn.execute(stmt)
            return int(result.inserted_primary_key[0])

    async def get_all(
        self,
        *,
        status: str | None = None,
        submitted_by_id: Any | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(contributor_claim_table).order_by(desc(contributor_claim_table.c.created_at))
        if status:
            stmt = stmt.where(contributor_claim_table.c.status == status)
        async with create_engine().connect() as conn:
            rows = (await conn.execute(stmt)).mappings().all()
        claims = [dict(row) for row in rows]
        if submitted_by_id is not None:
            claims = [
                claim
                for claim in claims
                if claim.get("submitted_by", {}).get("id") == submitted_by_id
            ]
        return claims

    async def get(self, claim_id: int) -> dict[str, Any] | None:
        stmt = select(contributor_claim_table).where(contributor_claim_table.c.id == claim_id)
        async with create_engine().connect() as conn:
            row = (await conn.execute(stmt)).mappings().first()
        return dict(row) if row else None

    async def review(
        self,
        *,
        claim_id: int,
        status: str,
        reviewer: dict[str, Any],
        comment: str,
    ) -> None:
        stmt = (
            update(contributor_claim_table)
            .where(contributor_claim_table.c.id == claim_id)
            .values(
                status=status,
                review={
                    "reviewer": reviewer,
                    "comment": comment,
                },
                reviewed_at=datetime.now(tz=timezone.utc),
            )
        )
        async with create_engine().begin() as conn:
            await conn.execute(stmt)

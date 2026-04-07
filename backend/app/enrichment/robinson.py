"""Lista Robinson management (Spain opt-out registry).

The Lista Robinson is maintained by ADIGITAL and contains phone numbers
of people who have opted out of commercial communications.

This module manages the local cache and provides lookup functionality.
The actual list must be obtained via formal request to ADIGITAL.
"""

import csv
import logging
from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.enrichment.phone_normalizer import normalize_phone_e164
from app.models.outreach import RobinsonEntry

logger = logging.getLogger(__name__)


async def import_robinson_csv(file_path: str, db: AsyncSession) -> int:
    """Import Lista Robinson from CSV file.

    Expected CSV format: one phone number per line (or column 'telefono').
    Replaces the entire existing list.

    Returns number of entries imported.
    """
    # Clear existing entries
    await db.execute(delete(RobinsonEntry))

    count = 0
    now = datetime.utcnow()

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            phone_raw = row[0].strip()
            phone_e164 = normalize_phone_e164(phone_raw, "ES")
            if phone_e164:
                entry = RobinsonEntry(phone_e164=phone_e164, checked_at=now)
                db.add(entry)
                count += 1

                if count % 10000 == 0:
                    await db.flush()

    await db.commit()
    logger.info(f"Imported {count} Robinson entries from {file_path}")
    return count


async def check_robinson(phone_e164: str, db: AsyncSession) -> bool:
    """Check if a phone number is in the Lista Robinson.

    Returns True if the number is listed (do not call).
    """
    if not phone_e164:
        return False

    from sqlalchemy import select

    stmt = select(RobinsonEntry).where(RobinsonEntry.phone_e164 == phone_e164)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None

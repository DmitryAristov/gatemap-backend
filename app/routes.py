from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy import select, func
from app.db import async_session
from app.models import LocationPing, Checkpoint, QueueReport, Feedback, Proposal, ProposalVote
from app.schemas import (
    LocationData, CheckpointOut, QueueReportCreate, QueueReportOut, 
    FeedbackCreate, ProposalOut, ProposalVoteResult, ProposalVoteCreate
)
from datetime import datetime, timezone
import uuid


router = APIRouter()


@router.get("/checkpoints", response_model=list[CheckpointOut])
async def get_checkpoints_in_bbox(
    min_lat: float = Query(..., description="Минимальная широта"),
    max_lat: float = Query(..., description="Максимальная широта"),
    min_lon: float = Query(..., description="Минимальная долгота"),
    max_lon: float = Query(..., description="Максимальная долгота"),
    db: AsyncSession = Depends(async_session)
):
    stmt = select(Checkpoint).where(
        Checkpoint.lat >= min_lat,
        Checkpoint.lat <= max_lat,
        Checkpoint.lon >= min_lon,
        Checkpoint.lon <= max_lon
    )
    result = await db.execute(stmt)
    checkpoints = result.scalars().all()

    return [
        CheckpointOut(
            id=cp.id,
            name=cp.name,
            latitude=cp.lat,
            longitude=cp.lon,
            country_from=cp.country_from,
            country_to=cp.country_to,
            queueSize=cp.avg_queue_size,
            waitTimeHours=cp.avg_wait_time_hours,
            updatedAt=cp.avg_updated_at
        )
        for cp in checkpoints
    ]


@router.get("/checkpoints/{checkpoint_id}", response_model=CheckpointOut)
async def get_checkpoint_by_id(checkpoint_id: int, db: AsyncSession = Depends(async_session)):
    stmt = select(Checkpoint).where(Checkpoint.id == checkpoint_id)
    result = await db.execute(stmt)
    cp = result.scalar_one_or_none()

    if cp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint with id {checkpoint_id} not found"
        )

    return CheckpointOut(
        id=cp.id,
        name=cp.name,
        latitude=cp.lat,
        longitude=cp.lon,
        country_from=cp.country_from,
        country_to=cp.country_to,
        queueSize=cp.avg_queue_size,
        waitTimeHours=cp.avg_wait_time_hours,
        updatedAt=cp.avg_updated_at
    )


@router.post("/location")
async def save_location(
    data: LocationData,
    session: AsyncSession = Depends(async_session)
):
    stmt = select(Checkpoint.id).where(Checkpoint.id == data.checkpoint_id)
    result = await session.execute(stmt)
    if result.scalar() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint with id {data.checkpoint_id} not found"
        )

    new_entry = LocationPing(
        id=str(uuid.uuid4()),
        device_id=data.device_id,
        lat=data.latitude,
        lon=data.longitude,
        checkpoint_id=data.checkpoint_id,
        timestamp=datetime.now(timezone.utc)
    )
    session.add(new_entry)
    await session.commit()

    return {
        "status": "ok",
        "received_at": new_entry.timestamp.isoformat()
    }


@router.post("/queue_report", response_model=QueueReportOut)
async def submit_queue_report(
    report: QueueReportCreate,
    session: AsyncSession = Depends(async_session)
):
    stmt = select(Checkpoint).where(Checkpoint.id == report.checkpoint_id)
    result = await session.execute(stmt)
    checkpoint = result.scalar_one_or_none()
    if checkpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint with id {report.checkpoint_id} not found"
        )

    submitted_at = datetime.now(timezone.utc)

    stmt = pg_insert(QueueReport).values(
        id=str(uuid.uuid4()),
        checkpoint_id=report.checkpoint_id,
        lat=report.lat,
        lon=report.lon,
        waiting_time_hours=report.waiting_time_hours,
        throughput_vehicles_per_hour=report.throughput_vehicles_per_hour,
        device_id=report.device_id,
        submitted_at=submitted_at
    ).on_conflict_do_update(
        index_elements=["device_id", "checkpoint_id"],
        set_={
            "lat": report.lat,
            "lon": report.lon,
            "waiting_time_hours": report.waiting_time_hours,
            "throughput_vehicles_per_hour": report.throughput_vehicles_per_hour,
            "submitted_at": submitted_at
        }
    )

    await session.execute(stmt)
    await session.commit()

    return QueueReportOut(submitted_at=submitted_at)


@router.post("/feedback")
async def submit_feedback(data: FeedbackCreate, db: AsyncSession = Depends(async_session)):
    new_feedback = Feedback(
        id=uuid.uuid4(),
        message=data.message,
        tag=data.tag,
        email=data.email,
        logs=data.logs,
        submitted_at=datetime.now(timezone.utc)
    )
    db.add(new_feedback)
    await db.commit()
    return {"status": "ok"}


@router.get("/proposals", response_model=list[ProposalOut])
async def get_proposals(db: AsyncSession = Depends(async_session)):
    stmt = select(Proposal)
    result = await db.execute(stmt)
    proposals = result.scalars().all()

    out = []
    for p in proposals:
        votes_stmt = select(
            func.count().filter(ProposalVote.vote == True),
            func.count().filter(ProposalVote.vote == False)
        ).where(ProposalVote.proposal_id == p.id)
        res = await db.execute(votes_stmt)
        upvotes, downvotes = res.fetchone()
        out.append(ProposalOut(
            id=p.id,
            title=p.title,
            description=p.description,
            created_at=p.created_at,
            upvotes=upvotes or 0,
            downvotes=downvotes or 0
        ))

    return out


@router.post("/proposals/{proposal_id}/vote", response_model=ProposalVoteResult)
async def vote_proposal(
    proposal_id: str,
    vote_data: ProposalVoteCreate,
    db: AsyncSession = Depends(async_session)
):
    vote = ProposalVote(
        id=uuid.uuid4(),
        proposal_id=proposal_id,
        device_id=vote_data.device_id,
        vote=vote_data.vote,
        voted_at=datetime.now(timezone.utc)
    )
    db.add(vote)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="You have already voted for this proposal.")
    except DataError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal with id {proposal_id} not found"
        )

    stmt = select(
        func.count().filter(ProposalVote.vote == True),
        func.count().filter(ProposalVote.vote == False)
    ).where(ProposalVote.proposal_id == proposal_id)
    result = await db.execute(stmt)
    upvotes, downvotes = result.fetchone()

    return ProposalVoteResult(upvotes=upvotes or 0, downvotes=downvotes or 0)


@router.get("/", response_model=str)
async def get_hello_world():
    return "Hello, world!"

import datetime

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import models
from app.core.database.models.user import RoleType
from app.core.middleware import dependencies
from tests.functional.test_booking import authorize
from tests.functional.test_service import (
    create_service,
    create_service_type,
    create_user,
)


def future_start(days: int = 1) -> str:
    return (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()


async def create_booking_for_review(
    test_client: AsyncClient,
    test_app: FastAPI,
    test_session: AsyncSession,
    *,
    status: models.BookingStatus = models.BookingStatus.COMPLETED,
    slot_days: int = 1,
) -> tuple[models.User, models.User, models.Service, int]:
    master = await create_user(
        test_session,
        email=f"review-master-{slot_days}-{status.value}@example.com",
        role=RoleType.MASTER,
    )
    user = await create_user(
        test_session,
        email=f"review-user-{slot_days}-{status.value}@example.com",
        role=RoleType.USER,
    )
    service_type = await create_service_type(
        test_session,
        name=f"Review service type {slot_days} {status.value}",
    )
    service = await create_service(
        test_session,
        master=master,
        service_type=service_type,
        duration_minutes=60,
    )

    await authorize(test_app, master)
    pool_response = await test_client.post(
        "/booking/availability/pool",
        json={
            "start_time": future_start(slot_days),
            "slot_duration_minutes": 60,
            "slots_count": 1,
        },
    )
    slot_id = pool_response.json()["data"][0]["id"]

    await authorize(test_app, user)
    booking_response = await test_client.post(
        "/booking/create",
        json={"service_id": service.id, "availability_slot_id": slot_id},
    )
    booking_id = booking_response.json()["id"]

    if status == models.BookingStatus.CANCELLED:
        cancel_response = await test_client.patch(f"/booking/cancel/{booking_id}")
        assert cancel_response.status_code == 200, cancel_response.json()
    elif status != models.BookingStatus.PENDING:
        await authorize(test_app, master)
        status_response = await test_client.patch(
            f"/booking/change-status/{booking_id}",
            json={"status": status.value},
        )
        assert status_response.status_code == 200, status_response.json()

    return user, master, service, booking_id


@pytest.mark.asyncio
async def test_user_creates_review_only_for_completed_own_booking(
    test_client: AsyncClient,
    test_app: FastAPI,
    test_session: AsyncSession,
):
    user, master, service, booking_id = await create_booking_for_review(
        test_client,
        test_app,
        test_session,
    )

    await authorize(test_app, user)
    response = await test_client.post(
        "/review/create",
        json={"booking_id": booking_id, "rating": 5, "text": "Excellent"},
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["user_id"] == user.id, body
    assert body["master_id"] == master.id, body
    assert body["service_id"] == service.id, body
    assert body["booking_id"] == booking_id, body
    assert body["rating"] == 5, body
    assert body["text"] == "Excellent", body

    duplicate_response = await test_client.post(
        "/review/create",
        json={"booking_id": booking_id, "rating": 4, "text": "Again"},
    )
    assert duplicate_response.status_code == 409, duplicate_response.json()


@pytest.mark.asyncio
async def test_review_cannot_be_created_for_not_completed_or_foreign_booking(
    test_client: AsyncClient,
    test_app: FastAPI,
    test_session: AsyncSession,
):
    user, _, _, pending_booking_id = await create_booking_for_review(
        test_client,
        test_app,
        test_session,
        status=models.BookingStatus.PENDING,
        slot_days=2,
    )
    other_user = await create_user(
        test_session,
        email="foreign-review-user@example.com",
        role=RoleType.USER,
    )

    await authorize(test_app, user)
    pending_response = await test_client.post(
        "/review/create",
        json={"booking_id": pending_booking_id, "rating": 5},
    )
    assert pending_response.status_code == 400, pending_response.json()
    assert (
        pending_response.json()["detail"]
        == "Review can be created only for completed bookings"
    )

    await authorize(test_app, other_user)
    foreign_response = await test_client.post(
        "/review/create",
        json={"booking_id": pending_booking_id, "rating": 5},
    )
    assert foreign_response.status_code == 403, foreign_response.json()

    cancelled_user, _, _, cancelled_booking_id = await create_booking_for_review(
        test_client,
        test_app,
        test_session,
        status=models.BookingStatus.CANCELLED,
        slot_days=3,
    )
    await authorize(test_app, cancelled_user)
    cancelled_response = await test_client.post(
        "/review/create",
        json={"booking_id": cancelled_booking_id, "rating": 5},
    )
    assert cancelled_response.status_code == 400, cancelled_response.json()


@pytest.mark.asyncio
async def test_get_list_update_and_admin_delete_review(
    test_client: AsyncClient,
    test_app: FastAPI,
    test_session: AsyncSession,
):
    user, master, service, booking_id = await create_booking_for_review(
        test_client,
        test_app,
        test_session,
        slot_days=4,
    )
    stranger = await create_user(
        test_session,
        email="review-stranger@example.com",
        role=RoleType.USER,
    )
    admin = await create_user(
        test_session,
        email="review-admin@example.com",
        role=RoleType.ADMIN,
    )

    await authorize(test_app, user)
    create_response = await test_client.post(
        "/review/create",
        json={"booking_id": booking_id, "rating": 4, "text": "Good"},
    )
    review_id = create_response.json()["id"]

    get_response = await test_client.get(f"/review/{review_id}")
    assert get_response.status_code == 200, get_response.json()
    assert get_response.json()["id"] == review_id, get_response.json()

    list_response = await test_client.request(
        "GET",
        "/review/list",
        json={"filters": {"service_id": service.id, "master_id": master.id}},
    )
    list_body = list_response.json()
    assert list_response.status_code == 200, list_body
    assert list_body["total"] == 1, list_body
    assert list_body["data"][0]["id"] == review_id, list_body

    await authorize(test_app, stranger)
    forbidden_update_response = await test_client.patch(
        f"/review/{review_id}",
        json={"rating": 1, "text": "Not mine"},
    )
    assert (
        forbidden_update_response.status_code == 403
    ), forbidden_update_response.json()

    await authorize(test_app, user)
    update_response = await test_client.patch(
        f"/review/{review_id}",
        json={"rating": 5, "text": "Perfect"},
    )
    update_body = update_response.json()
    assert update_response.status_code == 200, update_body
    assert update_body["rating"] == 5, update_body
    assert update_body["text"] == "Perfect", update_body

    test_app.dependency_overrides[dependencies.require_admin] = lambda: admin
    delete_response = await test_client.delete(f"/review/{review_id}")
    assert delete_response.status_code == 200, delete_response.json()
    assert delete_response.json()["detail"] == "Review deleted"

    review = await test_session.scalar(
        select(models.Review).where(models.Review.id == review_id)
    )
    assert review is None

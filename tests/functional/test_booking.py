import datetime

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import models
from app.core.database.models.user import RoleType
from app.core.middleware import dependencies
from tests.functional.test_service import (
    create_service,
    create_service_type,
    create_user,
)


async def authorize(
    test_app: FastAPI,
    user: models.User,
) -> None:
    test_app.dependency_overrides[dependencies.get_current_user_dep] = lambda: user
    test_app.dependency_overrides.pop(dependencies.require_master_or_admin, None)
    if user.role in {RoleType.MASTER, RoleType.ADMIN}:
        test_app.dependency_overrides[dependencies.require_master_or_admin] = (
            lambda: user
        )


def future_start() -> str:
    return (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()


@pytest.mark.asyncio
async def test_master_creates_availability_pool_and_user_reads_free_slots(
    test_client: AsyncClient,
    test_app: FastAPI,
    test_session: AsyncSession,
):
    master = await create_user(
        test_session,
        email="booking-master@example.com",
        role=RoleType.MASTER,
    )
    await authorize(test_app, master)

    response = await test_client.post(
        "/booking/availability/pool",
        json={
            "start_time": future_start(),
            "slot_duration_minutes": 60,
            "slots_count": 2,
        },
    )
    body = response.json()

    assert response.status_code == 200, body
    assert len(body["data"]) == 2, body
    assert body["data"][0]["master_id"] == master.id, body
    assert body["data"][0]["is_booked"] is False, body

    list_response = await test_client.request(
        "GET",
        f"/booking/availability/{master.id}",
        json={"filters": {"include_booked": False}},
    )
    list_body = list_response.json()

    assert list_response.status_code == 200, list_body
    assert list_body["total"] == 2, list_body


@pytest.mark.asyncio
async def test_user_books_existing_slot_and_slot_becomes_booked(
    test_client: AsyncClient,
    test_app: FastAPI,
    test_session: AsyncSession,
):
    master = await create_user(
        test_session,
        email="slot-master@example.com",
        role=RoleType.MASTER,
    )
    user = await create_user(
        test_session,
        email="slot-user@example.com",
        role=RoleType.USER,
    )
    service_type = await create_service_type(test_session, "Booking manicure")
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
            "start_time": future_start(),
            "slot_duration_minutes": 60,
            "slots_count": 1,
        },
    )
    slot_id = pool_response.json()["data"][0]["id"]

    await authorize(test_app, user)
    response = await test_client.post(
        "/booking/create",
        json={"service_id": service.id, "availability_slot_id": slot_id},
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["user_id"] == user.id, body
    assert body["master_id"] == master.id, body
    assert body["status"] == "PENDING", body

    slot = await test_session.scalar(
        select(models.MasterAvailabilitySlot).where(
            models.MasterAvailabilitySlot.id == slot_id
        )
    )
    assert slot.is_booked is True

    duplicate_response = await test_client.post(
        "/booking/create",
        json={"service_id": service.id, "availability_slot_id": slot_id},
    )
    assert duplicate_response.status_code == 409, duplicate_response.json()


@pytest.mark.asyncio
async def test_booking_fails_when_slot_does_not_belong_to_service_master(
    test_client: AsyncClient,
    test_app: FastAPI,
    test_session: AsyncSession,
):
    service_master = await create_user(
        test_session,
        email="service-owner@example.com",
        role=RoleType.MASTER,
    )
    slot_master = await create_user(
        test_session,
        email="slot-owner@example.com",
        role=RoleType.MASTER,
    )
    user = await create_user(
        test_session,
        email="wrong-slot-user@example.com",
        role=RoleType.USER,
    )
    service_type = await create_service_type(test_session, "Wrong slot service")
    service = await create_service(
        test_session,
        master=service_master,
        service_type=service_type,
        duration_minutes=60,
    )

    await authorize(test_app, slot_master)
    pool_response = await test_client.post(
        "/booking/availability/pool",
        json={
            "start_time": future_start(),
            "slot_duration_minutes": 60,
            "slots_count": 1,
        },
    )
    slot_id = pool_response.json()["data"][0]["id"]

    await authorize(test_app, user)
    response = await test_client.post(
        "/booking/create",
        json={"service_id": service.id, "availability_slot_id": slot_id},
    )

    assert response.status_code == 400, response.json()
    assert (
        response.json()["detail"]
        == "Availability slot does not belong to service master"
    )


@pytest.mark.asyncio
async def test_master_changes_booking_status_and_user_cancels_booking(
    test_client: AsyncClient,
    test_app: FastAPI,
    test_session: AsyncSession,
):
    master = await create_user(
        test_session,
        email="status-master@example.com",
        role=RoleType.MASTER,
    )
    user = await create_user(
        test_session,
        email="status-user@example.com",
        role=RoleType.USER,
    )
    service_type = await create_service_type(test_session, "Status service")
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
            "start_time": future_start(),
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

    await authorize(test_app, master)
    confirm_response = await test_client.patch(
        f"/booking/change-status/{booking_id}",
        json={"status": "CONFIRMED"},
    )
    assert confirm_response.status_code == 200, confirm_response.json()
    assert confirm_response.json()["status"] == "CONFIRMED"

    await authorize(test_app, user)
    cancel_response = await test_client.patch(f"/booking/cancel/{booking_id}")
    assert cancel_response.status_code == 200, cancel_response.json()
    assert cancel_response.json()["status"] == "CANCELLED"

    slot = await test_session.scalar(
        select(models.MasterAvailabilitySlot).where(
            models.MasterAvailabilitySlot.id == slot_id
        )
    )
    assert slot.is_booked is False

    rebook_response = await test_client.post(
        "/booking/create",
        json={"service_id": service.id, "availability_slot_id": slot_id},
    )
    assert rebook_response.status_code == 200, rebook_response.json()
    assert rebook_response.json()["status"] == "PENDING"


@pytest.mark.asyncio
async def test_booking_list_is_scoped_by_current_user_without_id_filters(
    test_client: AsyncClient,
    test_app: FastAPI,
    test_session: AsyncSession,
):
    first_master = await create_user(
        test_session,
        email="list-first-master@example.com",
        role=RoleType.MASTER,
    )
    second_master = await create_user(
        test_session,
        email="list-second-master@example.com",
        role=RoleType.MASTER,
    )
    first_user = await create_user(
        test_session,
        email="list-first-user@example.com",
        role=RoleType.USER,
    )
    second_user = await create_user(
        test_session,
        email="list-second-user@example.com",
        role=RoleType.USER,
    )
    first_service_type = await create_service_type(test_session, "List first service")
    second_service_type = await create_service_type(test_session, "List second service")
    first_service = await create_service(
        test_session,
        master=first_master,
        service_type=first_service_type,
        duration_minutes=60,
    )
    second_service = await create_service(
        test_session,
        master=second_master,
        service_type=second_service_type,
        duration_minutes=60,
    )

    await authorize(test_app, first_master)
    first_pool_response = await test_client.post(
        "/booking/availability/pool",
        json={
            "start_time": future_start(),
            "slot_duration_minutes": 60,
            "slots_count": 1,
        },
    )
    first_slot_id = first_pool_response.json()["data"][0]["id"]

    await authorize(test_app, second_master)
    second_pool_response = await test_client.post(
        "/booking/availability/pool",
        json={
            "start_time": (
                datetime.datetime.now() + datetime.timedelta(days=2)
            ).isoformat(),
            "slot_duration_minutes": 60,
            "slots_count": 1,
        },
    )
    second_slot_id = second_pool_response.json()["data"][0]["id"]

    await authorize(test_app, first_user)
    first_booking_response = await test_client.post(
        "/booking/create",
        json={
            "service_id": first_service.id,
            "availability_slot_id": first_slot_id,
        },
    )
    first_booking_id = first_booking_response.json()["id"]

    await authorize(test_app, second_user)
    second_booking_response = await test_client.post(
        "/booking/create",
        json={
            "service_id": second_service.id,
            "availability_slot_id": second_slot_id,
        },
    )
    second_booking_id = second_booking_response.json()["id"]

    await authorize(test_app, first_user)
    user_list_response = await test_client.request("GET", "/booking/list", json={})
    user_list_body = user_list_response.json()

    assert user_list_response.status_code == 200, user_list_body
    assert user_list_body["total"] == 1, user_list_body
    assert user_list_body["data"][0]["id"] == first_booking_id, user_list_body

    await authorize(test_app, second_master)
    master_list_response = await test_client.request("GET", "/booking/list", json={})
    master_list_body = master_list_response.json()

    assert master_list_response.status_code == 200, master_list_body
    assert master_list_body["total"] == 1, master_list_body
    assert master_list_body["data"][0]["id"] == second_booking_id, master_list_body

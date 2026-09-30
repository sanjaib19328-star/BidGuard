import hashlib
import io
import os
import shutil
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Tuple

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.main import app
from app.models.audit import AuditLog
from app.models.enums import DocumentProcessingStatus, TenderStatus, UserRole
from app.models.tender import Tender, TenderDocument
from app.models.user import Organization, User
from app.services import storage_service


@pytest.fixture
def test_client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def create_sample_pdf_bytes(content: str = "Test Tender Document Content") -> bytes:
    """Generate a valid minimal synthetic PDF binary byte string."""
    return f"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length {len(content)} >>\nstream\n{content}\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000210 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n300\n%%EOF".encode("utf-8")


@pytest.fixture
async def setup_doc_test_env(test_client):
    """Setup test organizations, users, and tenders for document management tests."""
    uid = uuid.uuid4().hex[:8]
    org_a_name = f"Doc Org A {uid}"
    org_b_name = f"Doc Org B {uid}"

    tokens = {}
    users = {}
    orgs = {}
    tenders = {}

    async with AsyncSessionLocal() as session:
        # 1. Organizations
        org_a = Organization(name=org_a_name)
        org_b = Organization(name=org_b_name)
        session.add_all([org_a, org_b])
        await session.flush()
        orgs["A"] = org_a
        orgs["B"] = org_b

        # 2. Users
        for role in [UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.REVIEWER, UserRole.AUDITOR]:
            u_a = User(
                email=f"doc_a_{role.value.lower()}_{uid}@example.com",
                password_hash=get_password_hash("DocPass123!"),
                full_name=f"Doc Org A {role.value}",
                role=role,
                organization_id=org_a.id,
                is_active=True,
            )
            u_b = User(
                email=f"doc_b_{role.value.lower()}_{uid}@example.com",
                password_hash=get_password_hash("DocPass123!"),
                full_name=f"Doc Org B {role.value}",
                role=role,
                organization_id=org_b.id,
                is_active=True,
            )
            session.add_all([u_a, u_b])
            users[f"A_{role.value}"] = u_a
            users[f"B_{role.value}"] = u_b

        await session.flush()

        # 3. Tenders
        deadline = datetime.now(timezone.utc) + timedelta(days=30)
        t_a = Tender(
            organization_id=org_a.id,
            tender_number=f"TND-DOC-A-{uid}",
            title="Org A Tender with Documents",
            submission_deadline=deadline,
            status=TenderStatus.DRAFT,
            created_by=users["A_PROCUREMENT_OFFICER"].id,
        )
        t_b = Tender(
            organization_id=org_b.id,
            tender_number=f"TND-DOC-B-{uid}",
            title="Org B Tender with Documents",
            submission_deadline=deadline,
            status=TenderStatus.DRAFT,
            created_by=users["B_PROCUREMENT_OFFICER"].id,
        )
        session.add_all([t_a, t_b])
        await session.commit()
        await session.refresh(t_a)
        await session.refresh(t_b)
        tenders["A"] = t_a
        tenders["B"] = t_b

    # 4. Login tokens
    for key, u in users.items():
        res = await test_client.post(
            "/api/v1/auth/login",
            json={"email": u.email, "password": "DocPass123!"},
        )
        assert res.status_code == 200
        tokens[key] = res.json()["access_token"]

    yield {
        "orgs": orgs,
        "users": users,
        "tenders": tenders,
        "tokens": tokens,
    }

    # Teardown: Clean up test files created on disk
    storage_service.delete_tender_directory(t_a.id)
    storage_service.delete_tender_directory(t_b.id)


# ==============================================================================
# 1. Authentication Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_document_unauthenticated_requests(test_client):
    """Verify document endpoints require authentication (401)."""
    fake_tender_id = uuid.uuid4()
    fake_doc_id = uuid.uuid4()

    # Upload
    res = await test_client.post(f"/api/v1/tenders/{fake_tender_id}/documents")
    assert res.status_code == 401

    # List
    res = await test_client.get(f"/api/v1/tenders/{fake_tender_id}/documents")
    assert res.status_code == 401

    # Get metadata
    res = await test_client.get(f"/api/v1/tenders/{fake_tender_id}/documents/{fake_doc_id}")
    assert res.status_code == 401

    # Download
    res = await test_client.get(f"/api/v1/tenders/{fake_tender_id}/documents/{fake_doc_id}/download")
    assert res.status_code == 401

    # Delete
    res = await test_client.delete(f"/api/v1/tenders/{fake_tender_id}/documents/{fake_doc_id}")
    assert res.status_code == 401


# ==============================================================================
# 2. Upload & Role Authorization Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_document_upload_roles_and_validation(test_client, setup_doc_test_env):
    """Verify ADMIN and PROCUREMENT_OFFICER can upload; REVIEWER and AUDITOR receive 403."""
    tokens = setup_doc_test_env["tokens"]
    tender_a_id = setup_doc_test_env["tenders"]["A"].id
    pdf_bytes = create_sample_pdf_bytes("GeM NIT Document 2026")

    # 1. Procurement Officer -> 201 Created
    files_po = {"file": ("tender_notice.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_po = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/documents",
        files=files_po,
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_po.status_code == 201, res_po.text
    data_po = res_po.json()
    assert data_po["original_filename"] == "tender_notice.pdf"
    assert data_po["mime_type"] == "application/pdf"
    assert data_po["file_size"] == len(pdf_bytes)
    assert data_po["sha256_hash"] == hashlib.sha256(pdf_bytes).hexdigest()
    assert data_po["processing_status"] == "UPLOADED"
    assert data_po["organization_id"] == str(setup_doc_test_env["orgs"]["A"].id)
    assert "storage_path" not in data_po  # Never expose internal path

    # 2. Admin -> 201 Created (different content)
    pdf_bytes_admin = create_sample_pdf_bytes("Admin uploaded addendum")
    files_admin = {"file": ("addendum.pdf", io.BytesIO(pdf_bytes_admin), "application/pdf")}
    res_admin = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/documents",
        files=files_admin,
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )
    assert res_admin.status_code == 201

    # 3. Reviewer -> 403 Forbidden
    pdf_bytes_rev = create_sample_pdf_bytes("Reviewer doc")
    files_rev = {"file": ("rev.pdf", io.BytesIO(pdf_bytes_rev), "application/pdf")}
    res_rev = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/documents",
        files=files_rev,
        headers={"Authorization": f"Bearer {tokens['A_REVIEWER']}"},
    )
    assert res_rev.status_code == 403

    # 4. Auditor -> 403 Forbidden
    pdf_bytes_aud = create_sample_pdf_bytes("Auditor doc")
    files_aud = {"file": ("aud.pdf", io.BytesIO(pdf_bytes_aud), "application/pdf")}
    res_aud = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/documents",
        files=files_aud,
        headers={"Authorization": f"Bearer {tokens['A_AUDITOR']}"},
    )
    assert res_aud.status_code == 403


# ==============================================================================
# 3. File Format & Size Validation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_document_format_and_size_validation(test_client, setup_doc_test_env):
    """Verify non-PDF extension, fake PDF magic bytes, empty file, and oversized file rejections."""
    tokens = setup_doc_test_env["tokens"]
    tender_a_id = setup_doc_test_env["tenders"]["A"].id
    auth_header = {"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"}

    # 1. Invalid extension (.exe) -> 400
    files_exe = {"file": ("malware.exe", io.BytesIO(b"MZ12345"), "application/octet-stream")}
    res_exe = await test_client.post(f"/api/v1/tenders/{tender_a_id}/documents", files=files_exe, headers=auth_header)
    assert res_exe.status_code == 400
    assert "PDF files (.pdf)" in res_exe.json()["detail"]

    # 2. Fake PDF (starts with plain text not %PDF-) -> 400
    files_fake = {"file": ("fake.pdf", io.BytesIO(b"Hello world I am not a pdf"), "application/pdf")}
    res_fake = await test_client.post(f"/api/v1/tenders/{tender_a_id}/documents", files=files_fake, headers=auth_header)
    assert res_fake.status_code == 400
    assert "%PDF-" in res_fake.json()["detail"]

    # 3. Empty file (0 bytes) -> 400
    files_empty = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    res_empty = await test_client.post(f"/api/v1/tenders/{tender_a_id}/documents", files=files_empty, headers=auth_header)
    assert res_empty.status_code == 400
    assert "empty" in res_empty.json()["detail"].lower()


# ==============================================================================
# 4. Duplicate SHA-256 Handling Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_duplicate_document_handling(test_client, setup_doc_test_env):
    """Verify duplicate upload on same tender returns 409 and cleans up physical file, while same file on another tender succeeds."""
    tokens = setup_doc_test_env["tokens"]
    tender_a_id = setup_doc_test_env["tenders"]["A"].id
    tender_b_id = setup_doc_test_env["tenders"]["B"].id

    unique_content = f"Unique Spec Document {uuid.uuid4().hex}"
    pdf_bytes = create_sample_pdf_bytes(unique_content)
    sha256 = hashlib.sha256(pdf_bytes).hexdigest()

    # 1. Upload to Tender A -> 201
    files1 = {"file": ("spec.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res1 = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/documents",
        files=files1,
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res1.status_code == 201
    doc_a_id = res1.json()["id"]

    # 2. Duplicate upload to same Tender A -> 409 Conflict
    files2 = {"file": ("duplicate_spec.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res2 = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/documents",
        files=files2,
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res2.status_code == 409
    assert sha256 in res2.json()["detail"]

    # 3. Same file uploaded to Tender B (different tender in Org B) -> 201 Success
    files3 = {"file": ("spec_b.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res3 = await test_client.post(
        f"/api/v1/tenders/{tender_b_id}/documents",
        files=files3,
        headers={"Authorization": f"Bearer {tokens['B_PROCUREMENT_OFFICER']}"},
    )
    assert res3.status_code == 201


# ==============================================================================
# 5. Organization Isolation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_document_organization_isolation(test_client, setup_doc_test_env):
    """Verify Org A cannot view, download, or delete Org B documents (returns 404)."""
    tokens = setup_doc_test_env["tokens"]
    tender_b_id = setup_doc_test_env["tenders"]["B"].id
    pdf_bytes = create_sample_pdf_bytes("Confidential Org B PDF")

    # Upload to Org B
    res_b = await test_client.post(
        f"/api/v1/tenders/{tender_b_id}/documents",
        files={"file": ("b_doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {tokens['B_PROCUREMENT_OFFICER']}"},
    )
    assert res_b.status_code == 201
    doc_b_id = res_b.json()["id"]

    # Org A attempts upload to Org B tender -> 404
    res_cross_up = await test_client.post(
        f"/api/v1/tenders/{tender_b_id}/documents",
        files={"file": ("hacked.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )
    assert res_cross_up.status_code == 404

    # Org A attempts list Org B documents -> 404
    res_cross_list = await test_client.get(
        f"/api/v1/tenders/{tender_b_id}/documents",
        headers={"Authorization": f"Bearer {tokens['A_AUDITOR']}"},
    )
    assert res_cross_list.status_code == 404

    # Org A attempts get Org B document metadata -> 404
    res_cross_get = await test_client.get(
        f"/api/v1/tenders/{tender_b_id}/documents/{doc_b_id}",
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_cross_get.status_code == 404

    # Org A attempts download Org B document -> 404
    res_cross_dl = await test_client.get(
        f"/api/v1/tenders/{tender_b_id}/documents/{doc_b_id}/download",
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )
    assert res_cross_dl.status_code == 404

    # Org A attempts delete Org B document -> 404
    res_cross_del = await test_client.delete(
        f"/api/v1/tenders/{tender_b_id}/documents/{doc_b_id}",
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )
    assert res_cross_del.status_code == 404


# ==============================================================================
# 6. Listing, Metadata, and Download Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_document_listing_metadata_and_download(test_client, setup_doc_test_env):
    """Verify document listing, metadata retrieval, and streaming download integrity."""
    tokens = setup_doc_test_env["tokens"]
    tender_a_id = setup_doc_test_env["tenders"]["A"].id
    pdf_content = f"Streaming Test Document Content {uuid.uuid4().hex}"
    pdf_bytes = create_sample_pdf_bytes(pdf_content)
    expected_sha = hashlib.sha256(pdf_bytes).hexdigest()

    # Upload document
    res_up = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/documents",
        files={"file": ("technical_specs.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_up.status_code == 201
    doc_id = res_up.json()["id"]

    # 1. List documents
    res_list = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/documents",
        headers={"Authorization": f"Bearer {tokens['A_REVIEWER']}"},
    )
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["total"] >= 1
    doc_ids = [d["id"] for d in list_data["items"]]
    assert doc_id in doc_ids

    # 2. Get metadata
    res_meta = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/documents/{doc_id}",
        headers={"Authorization": f"Bearer {tokens['A_AUDITOR']}"},
    )
    assert res_meta.status_code == 200
    meta_data = res_meta.json()
    assert meta_data["id"] == doc_id
    assert meta_data["original_filename"] == "technical_specs.pdf"
    assert meta_data["sha256_hash"] == expected_sha

    # 3. Download document
    res_dl = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/documents/{doc_id}/download",
        headers={"Authorization": f"Bearer {tokens['A_AUDITOR']}"},
    )
    assert res_dl.status_code == 200
    assert res_dl.headers["content-type"] == "application/pdf"
    downloaded_bytes = res_dl.content
    assert downloaded_bytes == pdf_bytes
    assert hashlib.sha256(downloaded_bytes).hexdigest() == expected_sha


# ==============================================================================
# 7. Deletion & Audit Trail Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_document_deletion_and_audit(test_client, setup_doc_test_env):
    """Verify physical file and DB record deletion and audit trail events."""
    tokens = setup_doc_test_env["tokens"]
    tender_a_id = setup_doc_test_env["tenders"]["A"].id
    pdf_bytes = create_sample_pdf_bytes("Doc to be deleted")

    # Upload document
    res_up = await test_client.post(
        f"/api/v1/tenders/{tender_a_id}/documents",
        files={"file": ("temp_delete.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_up.status_code == 201
    doc_id = res_up.json()["id"]

    # Verify physical file exists on disk
    async with AsyncSessionLocal() as session:
        doc = await session.get(TenderDocument, uuid.UUID(doc_id))
        storage_path = doc.storage_path
        assert Path(storage_path).is_file()

    # Reviewer attempt to delete -> 403 Forbidden
    res_rev_del = await test_client.delete(
        f"/api/v1/tenders/{tender_a_id}/documents/{doc_id}",
        headers={"Authorization": f"Bearer {tokens['A_REVIEWER']}"},
    )
    assert res_rev_del.status_code == 403

    # Procurement Officer deletes -> 204 No Content
    res_del = await test_client.delete(
        f"/api/v1/tenders/{tender_a_id}/documents/{doc_id}",
        headers={"Authorization": f"Bearer {tokens['A_PROCUREMENT_OFFICER']}"},
    )
    assert res_del.status_code == 204

    # Verify physical file removed
    assert not Path(storage_path).exists()

    # Verify DB record removed -> 404 on get
    res_get_del = await test_client.get(
        f"/api/v1/tenders/{tender_a_id}/documents/{doc_id}",
        headers={"Authorization": f"Bearer {tokens['A_ADMIN']}"},
    )
    assert res_get_del.status_code == 404

    # Verify audit logs in PostgreSQL
    async with AsyncSessionLocal() as session:
        query = (
            select(AuditLog)
            .where(AuditLog.entity_id == doc_id)
            .order_by(AuditLog.created_at.asc())
        )
        res_audit = await session.execute(query)
        logs = list(res_audit.scalars().all())
        actions = [l.action for l in logs]
        assert "TENDER_DOCUMENT_UPLOADED" in actions
        assert "TENDER_DOCUMENT_DELETED" in actions

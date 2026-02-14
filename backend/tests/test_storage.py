"""Tests for storage helpers."""

import json

from src.utils import storage


def test_save_applicant_data_writes_json(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "get_storage_root", lambda: tmp_path)

    app_id = "app-123"
    applicant_data = {"name": "Asha", "age": 30}

    path = storage.save_applicant_data(app_id, applicant_data, metadata={"source": "test"})

    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["metadata"]["source"] == "test"
    assert payload["declared_data"]["name"] == "Asha"


def test_save_extracted_data_writes_json(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "get_storage_root", lambda: tmp_path)

    app_id = "app-456"
    extracted_data = {"cibil_score": 720}
    ocr_documents = [{"document_type": "cibil_report", "text": "score 720"}]

    path = storage.save_extracted_data(
        app_id,
        extracted_data,
        ocr_documents=ocr_documents,
        metadata={"request_type": "loan"}
    )

    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["metadata"]["request_type"] == "loan"
    assert payload["ocr_extracted_data"]["cibil_score"] == 720
    assert payload["ocr_documents"][0]["document_type"] == "cibil_report"

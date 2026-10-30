"""Seudonimización y desidentificación básica."""
from __future__ import annotations

import hashlib
import hmac
from typing import Any

# Lista mínima. En producción aplicar el perfil de desidentificación de DICOM PS3.15
# y revisar texto libre/píxeles quemados (burned-in) con un proceso validado.
DICOM_IDENTIFIER_KEYWORDS = (
    "PatientName", "PatientID", "PatientBirthDate", "PatientAddress",
    "OtherPatientIDs", "PatientTelephoneNumbers", "ReferringPhysicianName",
    "InstitutionName", "InstitutionAddress", "AccessionNumber",
)


def pseudonymize(identifier: str, key: str) -> str:
    """HMAC-SHA256 con clave secreta. Determinista: la institución puede recalcularlo
    desde la historia clínica, pero no es reversible sin esa clave."""
    if len(key) < 32:
        raise ValueError("La clave de seudonimización debe tener al menos 32 caracteres")
    digest = hmac.new(key.encode(), identifier.strip().encode(), hashlib.sha256).hexdigest()
    return "P-" + digest[:24]


def strip_dicom_identifiers(ds: Any) -> Any:
    for kw in DICOM_IDENTIFIER_KEYWORDS:
        if kw in ds:
            del ds[kw]
    return ds

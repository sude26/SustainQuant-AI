"""
SustainaQuant AI – PDF Metin Çıkarma
======================================
Sürdürülebilirlik raporlarından söylem metni çıkarır.
"""

import io
import re


def extract_text_from_pdf(file_bytes: bytes, max_pages: int = 30) -> str:
    """PDF dosyasından metin çıkarır."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(file_bytes))
    parts = []
    for i, page in enumerate(reader.pages):
        if i >= max_pages:
            break
        text = page.extract_text()
        if text:
            parts.append(text)

    raw = "\n".join(parts)
    return clean_extracted_text(raw)


def clean_extracted_text(text: str) -> str:
    """PDF artefaktlarını temizler."""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(\w)- (\w)", r"\1\2", text)
    return text.strip()


def detect_company_from_pdf(text: str, filename: str = "") -> str | None:
    """PDF dosya adı veya metinden şirket adını tahmin eder."""
    from data.esg_dataset import get_companies

    haystack = f"{filename} {text[:8000]}".lower()
    for company in get_companies():
        name = company["sirket_adi"].lower()
        bist = (company.get("bist_kodu") or "").lower()
        tokens = [name, bist, name.split()[0]]
        if any(token and token in haystack for token in tokens):
            return company["sirket_adi"]
    return None


def extract_esg_claims(text: str, max_chars: int = 2000) -> str:
    """
    Uzun rapordan ESG iddia cümlelerini önceliklendirir.
    Anahtar kelime içeren cümleleri birleştirir.
    """
    keywords = (
        "sürdürülebilir", "emisyon", "karbon", "enerji", "yenilenebilir",
        "net-zero", "su ", "atık", "geri dönüşüm", "çevre", "esg",
        "tasarruf", "azaltım", "hedef", "taahhüt", "iklim",
    )
    sentences = re.split(r"(?<=[.!?])\s+", text)
    matched = [s.strip() for s in sentences if any(k in s.lower() for k in keywords)]
    if not matched:
        return text[:max_chars]
    combined = " ".join(matched)
    return combined[:max_chars]

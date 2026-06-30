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


def _is_toc_noise(sentence: str) -> bool:
    """İçindekiler tablosu / XBRL placeholder cümlelerini eler."""
    s = sentence.strip()
    if len(s) < 55:
        return True
    if "[" in s and "]" in s:
        return True
    if re.search(r"(?i)(içindekiler|tablo \d|sayfa \d|yönetici özeti \d|rapor hakkında \d)", s):
        return True
    page_nums = re.findall(r"\b\d{1,3}\b", s)
    if len(page_nums) >= 4 and len(s) < 220:
        return True
    return False


def extract_esg_claims(text: str, max_chars: int = 2000) -> str:
    """
    Uzun rapordan ESG iddia cümlelerini önceliklendirir.
    İçindekiler ve şablon metinleri atlar; somut iddiaları seçer.
    """
    keywords = (
        "sürdürülebilir", "emisyon", "karbon", "enerji", "yenilenebilir",
        "net-zero", "ges", "su ", "atık", "geri dönüşüm", "çevre", "esg",
        "tasarruf", "azaltım", "hedef", "taahhüt", "iklim", "mw", "kwh",
        "sera gazı", "scope", "kapsam",
    )
    sentences = re.split(r"(?<=[.!?])\s+", text)
    scored: list[tuple[int, str]] = []
    for raw in sentences:
        s = raw.strip()
        if _is_toc_noise(s):
            continue
        if not any(k in s.lower() for k in keywords):
            continue
        score = sum(2 for k in keywords if k in s.lower())
        if re.search(r"\d", s):
            score += 3
        if len(s) > 120:
            score += 1
        scored.append((score, s))

    scored.sort(key=lambda item: item[0], reverse=True)
    matched = [s for _, s in scored]
    if not matched:
        fallback = [s.strip() for s in sentences if len(s.strip()) > 80 and not _is_toc_noise(s)]
        matched = fallback[:12]
    if not matched:
        return text[:max_chars]
    combined = " ".join(matched)
    return combined[:max_chars]

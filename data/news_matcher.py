"""
SustainaQuant AI – Haber Eşleştirme
=====================================
Whitelist RSS kaynaklarından şirket + ESG anahtar kelime eşleşmesi.
"""

from __future__ import annotations

import re
import time
from datetime import datetime
from html import unescape
from typing import Optional
from xml.etree import ElementTree

import httpx

from config import SOURCE_WHITELIST

RSS_FEEDS = [
    {
        "name": "Anadolu Ajansı Ekonomi",
        "url": "https://www.aa.com.tr/tr/rss/default?cat=ekonomi",
        "whitelist_match": "Anadolu Ajansı",
    },
    {
        "name": "Anadolu Ajansı Güncel",
        "url": "https://www.aa.com.tr/tr/rss/default?cat=guncel",
        "whitelist_match": "Anadolu Ajansı",
    },
    {
        "name": "Anadolu Ajansı Dünya",
        "url": "https://www.aa.com.tr/tr/rss/default?cat=dunya",
        "whitelist_match": "Anadolu Ajansı",
    },
    {
        "name": "Anadolu Ajansı Bilim Teknoloji",
        "url": "https://www.aa.com.tr/tr/rss/default?cat=bilim-teknoloji",
        "whitelist_match": "Anadolu Ajansı",
    },
]

ESG_NEWS_KEYWORDS = (
    "sürdürülebilir", "esg", "çevre", "emisyon", "karbon", "iklim",
    "enerji", "yeşil", "atık", "su ", "sera gazı", "iklim değişikliği",
    "çed", "yenilenebilir",
)

COMPANY_ALIASES = {
    "Tüpraş": ["tüpraş", "tupras", "tuprs", "türk petrol rafinerileri"],
    "ASELSAN": ["aselsan", "asels"],
    "Ford Otosan": ["ford otosan", "froto"],
    "Türk Hava Yolları": ["türk hava yolları", "thy", "thyao"],
    "Ereğli Demir Çelik": ["ereğli", "erdemir", "eregl"],
    "BİM": ["bim", "bimas"],
    "Sabancı Holding": ["sabancı", "sahol", "enerjisa"],
    "Koç Holding": ["koç holding", "kchol"],
    "Garanti BBVA": ["garanti", "garan"],
    "Şişecam": ["şişecam", "sise"],
    "Petkim": ["petkim", "petkm"],
    "Enka İnşaat": ["enka", "enkai"],
    "Tofaş": ["tofaş", "toaso"],
    "Akbank": ["akbank", "akbnk"],
    "Koza Altın": ["koza altın", "kozal"],
    "SASA": ["sasa", "sasa polyester", "sasa polyester sanayi"],
}


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return unescape(re.sub(r"\s+", " ", text)).strip()


def _parse_rss_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def _aliases_for_company(company_name: str, bist_code: str) -> list[str]:
    if company_name in COMPANY_ALIASES:
        return COMPANY_ALIASES[company_name]
    code = (bist_code or "").lower()
    for key, aliases in COMPANY_ALIASES.items():
        if key.lower() == code or code in [a.lower() for a in aliases]:
            return aliases
    return []


def _company_terms(company_name: str, bist_code: str) -> list[str]:
    terms = [company_name.lower(), bist_code.lower()]
    # KAP tam unvanından kısa ticker (ör. "SASA POLYESTER..." → "sasa")
    first_token = company_name.split()[0].lower().rstrip(".,;")
    if len(first_token) >= 3:
        terms.append(first_token)
    for alias in _aliases_for_company(company_name, bist_code):
        terms.append(alias.lower())
    return list(dict.fromkeys(t for t in terms if t))


def _is_whitelisted_source(feed_name: str) -> bool:
    feed_lower = feed_name.lower()
    for src in SOURCE_WHITELIST:
        if any(part.lower() in feed_lower for part in src.split()):
            return True
    return "anadolu" in feed_lower


class NewsMatcher:
    """RSS tabanlı haber eşleştirici."""

    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout
        self._cache: dict[str, tuple[float, list[dict]]] = {}
        self._cache_ttl = 300.0

    def _fetch_feed(self, url: str) -> list[dict]:
        now = time.monotonic()
        cached = self._cache.get(url)
        if cached and now - cached[0] < self._cache_ttl:
            return cached[1]

        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "SustainQuant-AI/1.0"})
            resp.raise_for_status()
            root = ElementTree.fromstring(resp.content)

        items = []
        for item in root.findall(".//item"):
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            desc = _strip_html(item.findtext("description") or "")
            pub = item.findtext("pubDate") or item.findtext("dc:date", default="")
            items.append({
                "title": title.strip(),
                "link": link.strip(),
                "summary": desc[:500],
                "published": pub,
                "published_datetime": _parse_rss_date(pub),
            })

        self._cache[url] = (now, items)
        return items

    def search(
        self,
        company_name: str,
        bist_code: str,
        extra_keywords: list[str] | None = None,
        max_results: int = 5,
    ) -> list[dict]:
        """Şirket adı + ESG anahtar kelimeleriyle eşleşen haberleri döndürür."""
        terms = _company_terms(company_name, bist_code)
        keywords = list(ESG_NEWS_KEYWORDS)
        if extra_keywords:
            keywords.extend(k.lower() for k in extra_keywords)

        matches = []
        for feed in RSS_FEEDS:
            try:
                entries = self._fetch_feed(feed["url"])
            except Exception:
                continue

            for entry in entries:
                blob = f"{entry['title']} {entry['summary']}".lower()
                if not any(t in blob for t in terms):
                    continue
                if not any(k in blob for k in keywords):
                    continue

                score = sum(2 for t in terms if t in blob)
                score += sum(1 for k in keywords if k in blob)
                matches.append({
                    **entry,
                    "feed": feed["name"],
                    "source": feed["whitelist_match"],
                    "source_url": entry["link"],
                    "trusted": _is_whitelisted_source(feed["name"]),
                    "match_score": score,
                    "text": f"{entry['title']}. {entry['summary']}".strip(),
                })

        matches.sort(key=lambda x: x["match_score"], reverse=True)
        seen = set()
        unique = []
        for m in matches:
            key = m["link"] or m["title"]
            if key in seen:
                continue
            seen.add(key)
            unique.append(m)
            if len(unique) >= max_results:
                break
        return unique

    def build_action_text(self, matches: list[dict], max_chars: int = 2000) -> str:
        """Eşleşen haberlerden birleşik eylem metni üretir."""
        parts = []
        for m in matches:
            parts.append(f"[{m['feed']}] {m['text']}")
        combined = " ".join(parts)
        return combined[:max_chars]


_default_matcher: NewsMatcher | None = None


def get_news_matcher() -> NewsMatcher:
    global _default_matcher
    if _default_matcher is None:
        _default_matcher = NewsMatcher()
    return _default_matcher

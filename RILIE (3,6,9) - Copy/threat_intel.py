"""
threat_intel.py — RILIE'S THREAT RADAR
========================================
When RILIE feels threatened (BJJ ORANGE/RED, Krav triggers), she doesn't
just rely on static keyword lists. She polls real-world threat intelligence
feeds to understand if she's seeing known attack patterns.

9 publicly available, free, no-auth-required threat intel sources:
  1. URLhaus (abuse.ch) — malicious URLs
  2. MalwareBazaar (abuse.ch) — malware hashes & signatures
  3. SSL Blacklist (abuse.ch) — malicious SSL certificates
  4. DShield Top 20 (SANS ISC) — top attacking subnets
  5. Tor Exit Nodes — anonymization network endpoints
  6. PhishTank — verified phishing URLs
  7. OpenPhish — phishing URL feed
  8. FireHOL Level 1 — aggregated blocklist
  9. CISA Known Exploited Vulnerabilities — active CVEs

BBQE architecture: behavioral detection + real-time intelligence.
BJJ + Krav + live threat data = trained operator with comms.

Usage:
  - ConversationHealthMonitor drops below ORANGE → poll feeds
  - Krav Maga detects injection/exploitation → check if known pattern
  - Periodic background poll (like CuriosityEngine) to stay current
"""

import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger("threat_intel")

# ============================================================================
# FEED DEFINITIONS
# ============================================================================

@dataclass
class ThreatFeed:
    """A single threat intelligence feed source."""
    name: str
    url: str
    category: str       # "url", "ip", "hash", "domain", "cve", "mixed"
    format: str         # "csv", "json", "text", "xml"
    description: str
    poll_interval: int  # seconds between polls (3600 = hourly)
    last_poll: float = 0.0
    last_count: int = 0
    healthy: bool = True
    error: str = ""


# The 9 feeds — all free, all no-auth
THREAT_FEEDS: List[ThreatFeed] = [
    ThreatFeed(
        name="URLhaus",
        url="https://urlhaus.abuse.ch/downloads/csv_online/",
        category="url",
        format="csv",
        description="Malicious URLs actively distributing malware (abuse.ch)",
        poll_interval=3600,
    ),
    ThreatFeed(
        name="MalwareBazaar Recent",
        url="https://bazaar.abuse.ch/export/txt/md5/recent/",
        category="hash",
        format="text",
        description="Recent malware MD5 hashes (abuse.ch)",
        poll_interval=3600,
    ),
    ThreatFeed(
        name="SSL Blacklist",
        url="https://sslbl.abuse.ch/blacklist/sslipblacklist.csv",
        category="ip",
        format="csv",
        description="IPs associated with malicious SSL certificates (abuse.ch)",
        poll_interval=7200,
    ),
    ThreatFeed(
        name="DShield Top 20",
        url="https://www.dshield.org/block.txt",
        category="ip",
        format="text",
        description="Top 20 most active attacking subnets (SANS ISC)",
        poll_interval=3600,
    ),
    ThreatFeed(
        name="Tor Exit Nodes",
        url="https://check.torproject.org/torbulkexitlist",
        category="ip",
        format="text",
        description="Current Tor exit node IP addresses",
        poll_interval=7200,
    ),
    ThreatFeed(
        name="OpenPhish",
        url="https://openphish.com/feed.txt",
        category="url",
        format="text",
        description="Community phishing URL feed",
        poll_interval=3600,
    ),
    ThreatFeed(
        name="FireHOL Level 1",
        url="https://raw.githubusercontent.com/ktsaou/blocklist-ipsets/master/firehol_level1.netset",
        category="ip",
        format="text",
        description="Aggregated blocklist — most aggressive known attackers",
        poll_interval=7200,
    ),
    ThreatFeed(
        name="CISA KEV",
        url="https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        category="cve",
        format="json",
        description="CISA Known Exploited Vulnerabilities catalog",
        poll_interval=86400,  # Daily — doesn't change fast
    ),
    ThreatFeed(
        name="C2 Intel Domains",
        url="https://raw.githubusercontent.com/drb-ra/C2IntelFeeds/master/feeds/domainC2s.csv",
        category="domain",
        format="csv",
        description="Known Command & Control server domains",
        poll_interval=3600,
    ),
]


# ============================================================================
# THREAT INTEL CACHE
# ============================================================================

@dataclass
class ThreatIntelCache:
    """
    In-memory cache of threat intelligence data.
    Refreshed on schedule or on-demand when RILIE feels threatened.
    """
    malicious_urls: List[str] = field(default_factory=list)
    malicious_ips: List[str] = field(default_factory=list)
    malicious_domains: List[str] = field(default_factory=list)
    malicious_hashes: List[str] = field(default_factory=list)
    known_cves: List[Dict[str, str]] = field(default_factory=list)
    c2_domains: List[str] = field(default_factory=list)
    tor_exits: List[str] = field(default_factory=list)
    last_refresh: float = 0.0
    feed_status: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def total_indicators(self) -> int:
        """Total number of threat indicators loaded."""
        return (
            len(self.malicious_urls) +
            len(self.malicious_ips) +
            len(self.malicious_domains) +
            len(self.malicious_hashes) +
            len(self.known_cves) +
            len(self.c2_domains) +
            len(self.tor_exits)
        )

    def summary(self) -> Dict[str, Any]:
        """Summary for health checks and API exposure."""
        return {
            "total_indicators": self.total_indicators(),
            "malicious_urls": len(self.malicious_urls),
            "malicious_ips": len(self.malicious_ips),
            "malicious_domains": len(self.malicious_domains),
            "malicious_hashes": len(self.malicious_hashes),
            "known_cves": len(self.known_cves),
            "c2_domains": len(self.c2_domains),
            "tor_exits": len(self.tor_exits),
            "last_refresh": self.last_refresh,
            "feed_status": self.feed_status,
        }


# Module-level cache
_cache = ThreatIntelCache()


def get_cache() -> ThreatIntelCache:
    """Access the threat intel cache."""
    return _cache


# ============================================================================
# FEED POLLING ENGINE
# ============================================================================

def _fetch_feed(feed: ThreatFeed, fetch_fn: Optional[Callable] = None) -> List[str]:
    """
    Fetch a single feed and return raw lines.

    Args:
        feed: The ThreatFeed to poll.
        fetch_fn: Optional HTTP fetch function. If None, uses urllib.
                  Signature: fetch_fn(url: str) -> str (response text)

    Returns:
        List of raw lines from the feed.
    """
    try:
        if fetch_fn:
            text = fetch_fn(feed.url)
        else:
            import urllib.request
            req = urllib.request.Request(
                feed.url,
                headers={"User-Agent": "RILIE-ThreatIntel/1.0"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                text = resp.read().decode("utf-8", errors="replace")

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        feed.last_poll = time.time()
        feed.last_count = len(lines)
        feed.healthy = True
        feed.error = ""
        logger.info("Feed '%s' polled: %d lines", feed.name, len(lines))
        return lines

    except Exception as e:
        feed.healthy = False
        feed.error = str(e)[:200]
        logger.warning("Feed '%s' failed: %s", feed.name, e)
        return []


def _parse_abuse_csv(lines: List[str]) -> List[str]:
    """Parse abuse.ch CSV format — extract URLs/IPs from first column."""
    results = []
    for line in lines:
        if line.startswith('"') or line.startswith("id"):
            continue  # Skip header
        parts = line.split(",")
        if parts:
            val = parts[0].strip().strip('"')
            if val and not val.startswith("#"):
                results.append(val)
    return results


def _parse_text_lines(lines: List[str]) -> List[str]:
    """Parse simple text feeds — one indicator per line."""
    return [
        line for line in lines
        if line and not line.startswith("#") and not line.startswith("//")
    ]


def _parse_cisa_json(lines: List[str]) -> List[Dict[str, str]]:
    """Parse CISA KEV JSON feed."""
    import json
    try:
        text = "\n".join(lines)
        data = json.loads(text)
        vulns = data.get("vulnerabilities", [])
        return [
            {
                "cve": v.get("cveID", ""),
                "vendor": v.get("vendorProject", ""),
                "product": v.get("product", ""),
                "name": v.get("vulnerabilityName", ""),
                "action": v.get("requiredAction", ""),
            }
            for v in vulns[:500]  # Cap at 500 most recent
        ]
    except Exception as e:
        logger.warning("Failed to parse CISA JSON: %s", e)
        return []


def poll_all_feeds(
    force: bool = False,
    fetch_fn: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    Poll all 9 threat intel feeds that are due for refresh.

    Args:
        force: If True, poll all feeds regardless of schedule.
        fetch_fn: Optional HTTP fetch function for testing.

    Returns:
        Summary dict with poll results.
    """
    global _cache
    now = time.time()
    polled = 0
    skipped = 0
    failed = 0

    for feed in THREAT_FEEDS:
        # Check if due for refresh
        elapsed = now - feed.last_poll
        if not force and elapsed < feed.poll_interval:
            skipped += 1
            continue

        lines = _fetch_feed(feed, fetch_fn)
        if not lines:
            failed += 1
            _cache.feed_status[feed.name] = {
                "healthy": False, "error": feed.error, "count": 0,
            }
            continue

        # Parse and store based on category
        if feed.name == "URLhaus":
            parsed = _parse_abuse_csv(lines)
            _cache.malicious_urls = parsed[:10000]  # Cap
        elif feed.name == "MalwareBazaar Recent":
            _cache.malicious_hashes = _parse_text_lines(lines)[:5000]
        elif feed.name == "SSL Blacklist":
            parsed = _parse_abuse_csv(lines)
            # Merge with existing IPs (don't replace)
            existing = set(_cache.malicious_ips)
            existing.update(parsed)
            _cache.malicious_ips = list(existing)[:20000]
        elif feed.name == "DShield Top 20":
            _cache.malicious_ips.extend(_parse_text_lines(lines)[:100])
        elif feed.name == "Tor Exit Nodes":
            _cache.tor_exits = _parse_text_lines(lines)
        elif feed.name == "OpenPhish":
            # Merge with URLhaus URLs
            existing = set(_cache.malicious_urls)
            existing.update(_parse_text_lines(lines))
            _cache.malicious_urls = list(existing)[:15000]
        elif feed.name == "FireHOL Level 1":
            existing = set(_cache.malicious_ips)
            existing.update(_parse_text_lines(lines))
            _cache.malicious_ips = list(existing)[:30000]
        elif feed.name == "CISA KEV":
            _cache.known_cves = _parse_cisa_json(lines)
        elif feed.name == "C2 Intel Domains":
            _cache.c2_domains = _parse_abuse_csv(lines)[:5000]

        _cache.feed_status[feed.name] = {
            "healthy": True, "count": feed.last_count,
            "last_poll": feed.last_poll,
        }
        polled += 1

    _cache.last_refresh = now

    result = {
        "polled": polled,
        "skipped": skipped,
        "failed": failed,
        "total_indicators": _cache.total_indicators(),
        "timestamp": now,
    }
    logger.info("Threat intel refresh: polled=%d skipped=%d failed=%d total=%d",
                polled, skipped, failed, _cache.total_indicators())
    return result


# ============================================================================
# THREAT LOOKUP — check specific indicators against the cache
# ============================================================================

def check_url(url: str) -> bool:
    """Is this URL in our threat feeds?"""
    return url.lower().strip() in {u.lower() for u in _cache.malicious_urls}


def check_ip(ip: str) -> bool:
    """Is this IP in our threat feeds?"""
    return ip.strip() in set(_cache.malicious_ips)


def check_domain(domain: str) -> bool:
    """Is this domain a known C2 or malicious domain?"""
    d = domain.lower().strip()
    return (
        d in {x.lower() for x in _cache.c2_domains} or
        d in {x.lower() for x in _cache.malicious_domains}
    )


def check_hash(hash_str: str) -> bool:
    """Is this hash a known malware sample?"""
    return hash_str.lower().strip() in {h.lower() for h in _cache.malicious_hashes}


def check_tor_exit(ip: str) -> bool:
    """Is this IP a known Tor exit node?"""
    return ip.strip() in set(_cache.tor_exits)


def check_stimulus_for_threats(stimulus: str) -> Dict[str, Any]:
    """
    Scan a user's stimulus for embedded threat indicators.

    Checks for:
    - URLs that match malicious feed data
    - IP addresses that match threat feeds
    - Domains that match C2 feeds
    - Hashes that match malware samples

    This is the function Triangle calls when BJJ reaches ORANGE/RED
    or Krav detects something suspicious.

    Returns:
        {
            "threats_found": int,
            "malicious_urls": [...],
            "malicious_ips": [...],
            "malicious_domains": [...],
            "malicious_hashes": [...],
            "tor_exits": [...],
        }
    """
    import re

    result: Dict[str, Any] = {
        "threats_found": 0,
        "malicious_urls": [],
        "malicious_ips": [],
        "malicious_domains": [],
        "malicious_hashes": [],
        "tor_exits": [],
    }

    # Extract URLs from stimulus
    urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', stimulus)
    for url in urls:
        if check_url(url):
            result["malicious_urls"].append(url)
            result["threats_found"] += 1

    # Extract IP addresses
    ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', stimulus)
    for ip in ips:
        if check_ip(ip):
            result["malicious_ips"].append(ip)
            result["threats_found"] += 1
        if check_tor_exit(ip):
            result["tor_exits"].append(ip)
            result["threats_found"] += 1

    # Extract potential domains
    domains = re.findall(r'\b[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}\b', stimulus)
    for domain in domains:
        if check_domain(domain):
            result["malicious_domains"].append(domain)
            result["threats_found"] += 1

    # Extract potential hashes (MD5/SHA1/SHA256)
    hashes = re.findall(r'\b[a-fA-F0-9]{32,64}\b', stimulus)
    for h in hashes:
        if check_hash(h):
            result["malicious_hashes"].append(h)
            result["threats_found"] += 1

    if result["threats_found"] > 0:
        logger.warning("Stimulus contains %d known threat indicators!",
                       result["threats_found"])

    return result


# ============================================================================
# THREAT INTEL STATUS — for API/health endpoints
# ============================================================================

def get_threat_intel_status() -> Dict[str, Any]:
    """Full status of the threat intel system."""
    return {
        "cache": _cache.summary(),
        "feeds": [
            {
                "name": f.name,
                "category": f.category,
                "healthy": f.healthy,
                "last_poll": f.last_poll,
                "last_count": f.last_count,
                "poll_interval": f.poll_interval,
                "error": f.error,
            }
            for f in THREAT_FEEDS
        ],
        "total_feeds": len(THREAT_FEEDS),
        "healthy_feeds": sum(1 for f in THREAT_FEEDS if f.healthy),
    }

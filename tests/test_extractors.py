from app.core.extractors import (
    extract_urls,
    extract_domains,
    extract_emails,
    extract_phones,
    is_shortener_domain,
    is_punycode_domain,
    subdomain_count,
)

def test_extract_urls_trims_punctuation_and_wrappers():
    text = 'Click (https://example.com/path?a=1), then "https://x.com/abc"...'
    urls = extract_urls(text)
    assert urls == ["https://example.com/path?a=1", "https://x.com/abc"]

def test_extract_domains_normalizes_www_and_ports():
    urls = ["https://www.Example.com:443/a", "http://sub.example.com/b"]
    domains = extract_domains(urls)
    assert domains == ["example.com", "sub.example.com"]

def test_extract_emails_unique_lowercase():
    text = "Contact Me: Admin@Example.com and admin@example.com"
    emails = extract_emails(text)
    assert emails == ["admin@example.com"]

def test_extract_phones_conservative():
    text = "Call +1 (212) 555-1234 or 03-555-1234. Ref: 12345"
    phones = extract_phones(text)
    assert "+12125551234" in phones or "12125551234" in phones
    assert any(p.endswith("035551234") or p.endswith("35551234") for p in phones)

def test_helpers():
    assert is_shortener_domain("bit.ly")
    assert is_shortener_domain("www.t.co")
    assert is_punycode_domain("xn--pple-43d.com")
    assert subdomain_count("a.b.c.example.com") == 5

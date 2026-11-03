# scala-score

[![CI](https://github.com/Alessandro114/scala-score-python/actions/workflows/ci.yml/badge.svg)](https://github.com/Alessandro114/scala-score-python/actions/workflows/ci.yml) [![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/Alessandro114/scala-score-python/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/scala-score)](https://pypi.org/project/scala-score/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Companies](https://img.shields.io/badge/companies-249M%2B-green)](https://get-scala.com/score)

**Python SDK for [S.C.A.L.A. Score API](https://get-scala.com/score)** — search 249M+ companies in 264 countries.

## Install

```bash
pip install scala-score
```

## Quick Start

```python
from scala_score import ScalaScore

score = ScalaScore("your-api-key")

# Search companies
results = score.search("Ferrero", country="IT")
for company in results.companies:
    print(f"{company.name} — {company.city} — Revenue: €{company.revenue:,.0f}")

# Lookup by VAT number
company = score.lookup("IT02727330014")
print(f"{company.name}: health score {company.health_score}/100")

# Generate a report
report = score.report("IT02727330014", report_type="pro")
print(f"Report: {report.download_url}")

# Check credits
credits = score.credits()
print(f"Remaining: {credits['credits_remaining']} credits")

# Database stats
stats = score.stats()
print(f"Total companies: {stats['total_companies']:,}")
```

## Search with Filters

```python
# Find active restaurants in Milan
results = score.search(
    "ristorante",
    country="IT",
    nace="56.10",      # NACE code for restaurants
    status="active",
    limit=50
)

# Find construction companies in Germany
results = score.search("bau", country="DE", nace="41", limit=20)

# Find tech companies in Spain
results = score.search("tecnología", country="ES", nace="62.01")
```

## Company Data Fields

Each company includes (when available):

| Field | Description |
|-------|-------------|
| `name` | Company legal name |
| `country` | ISO 2-letter code |
| `vat_number` | VAT / Tax ID |
| `address`, `city`, `postal_code` | Location |
| `nace_code`, `nace_description` | Industry classification |
| `legal_form` | SRL, GmbH, Ltd, SA, etc. |
| `status` | Active / Inactive / Dissolved |
| `revenue` | Estimated annual revenue (€) |
| `employees` | Employee count |
| `health_score` | Financial health (0-100) |
| `founded` | Incorporation date |
| `website`, `phone`, `email` | Contact info |

## Coverage

249M+ companies in 264 countries including:

| Country | Companies | Source |
|---------|-----------|-------|
| 🇮🇹 Italy | 6.2M | Camera di Commercio |
| 🇩🇪 Germany | 5.4M | Handelsregister |
| 🇫🇷 France | 29.5M | SIRENE/INSEE |
| 🇬🇧 UK | 5.8M | Companies House |
| 🇪🇸 Spain | 3.7M | BORME |
| 🇺🇸 USA | 35M+ | SEC + State registries |
| 🇳🇱 Netherlands | 2.8M | KVK |
| + 33 more countries | ... | Government registries |

## Pricing

| Plan | Price | Credits/mo | Per lookup |
|------|-------|-----------|-----------|
| Starter | €19/mo | 500 | €0.038 |
| Growth | €49/mo | 5,000 | €0.010 |
| Enterprise | €149/mo | 50,000 | €0.003 |

Compare: Dun & Bradstreet charges €2-5 per lookup. ZoomInfo starts at $15K/year.

## Get API Key

1. Sign up at [app.get-scala.com](https://app.get-scala.com)
2. Go to **Score > API**
3. Generate your key
4. `pip install scala-score` and start searching

## Links

- [API Documentation](https://app.get-scala.com/api/docs/ui)
- [S.C.A.L.A. AI OS](https://get-scala.com) — Full platform with CRM, WhatsApp AI, 15 industry verticals
- [n8n Integration](https://github.com/Alessandro114/n8n-nodes-scala)

## License

MIT

## Data coverage

S.C.A.L.A. Score holds about 249 million company records from public registries and open data in 264 countries (home page of [score.get-scala.com](https://score.get-scala.com): "Data from official registries in 264 countries · 249,353,619 companies", checked 03/11/2026). Not all records have financial data, and coverage varies by country: revenue, employees and score are shown only where the source publishes them. Always check each field before relying on it.

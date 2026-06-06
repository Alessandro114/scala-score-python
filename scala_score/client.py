"""S.C.A.L.A. Score API client."""

from __future__ import annotations
import httpx
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Company:
    id: str
    name: str
    country: str
    vat_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    nace_code: Optional[str] = None
    nace_description: Optional[str] = None
    legal_form: Optional[str] = None
    status: Optional[str] = None
    revenue: Optional[float] = None
    employees: Optional[int] = None
    health_score: Optional[float] = None
    founded: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> Company:
        return cls(
            id=data.get("id", ""),
            name=data.get("name", data.get("company_name", "")),
            country=data.get("country", data.get("country_code", "")),
            vat_number=data.get("vat_number", data.get("tax_id")),
            address=data.get("address", data.get("street")),
            city=data.get("city"),
            postal_code=data.get("postal_code", data.get("zip")),
            nace_code=data.get("nace_code", data.get("nace")),
            nace_description=data.get("nace_description"),
            legal_form=data.get("legal_form"),
            status=data.get("status"),
            revenue=data.get("revenue", data.get("estimated_revenue")),
            employees=data.get("employees", data.get("employee_count")),
            health_score=data.get("health_score", data.get("score")),
            founded=data.get("founded", data.get("incorporation_date")),
            website=data.get("website"),
            phone=data.get("phone"),
            email=data.get("email"),
            raw=data,
        )


@dataclass
class SearchResult:
    companies: list[Company]
    total: int
    query: str
    credits_used: int

    @classmethod
    def from_response(cls, data: dict, query: str) -> SearchResult:
        companies_data = data.get("results", data.get("companies", data.get("data", [])))
        return cls(
            companies=[Company.from_dict(c) for c in companies_data],
            total=data.get("total", len(companies_data)),
            query=query,
            credits_used=data.get("credits_used", 1),
        )


@dataclass
class ReportResult:
    report_id: str
    company_id: str
    type: str
    status: str
    download_url: Optional[str] = None
    raw: dict = field(default_factory=dict)


class ScalaScore:
    """Client for S.C.A.L.A. Score API — 244M+ companies worldwide.

    Usage:
        >>> from scala_score import ScalaScore
        >>> score = ScalaScore("your-api-key")
        >>> results = score.search("Ferrero", country="IT")
        >>> for company in results.companies:
        ...     print(f"{company.name} — {company.city} — Revenue: {company.revenue}")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://app.get-scala.com",
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            timeout=timeout,
        )

    def search(
        self,
        query: str,
        *,
        country: Optional[str] = None,
        nace: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> SearchResult:
        """Search companies by name, VAT, or keyword.

        Args:
            query: Company name, VAT number, or keyword
            country: ISO 2-letter country code (IT, DE, FR, US, GB, ...)
            nace: NACE industry code (e.g. "56.10" for restaurants)
            status: Filter by status ("active" or "inactive")
            limit: Max results (1-100, default 10)

        Returns:
            SearchResult with list of matching companies

        Example:
            >>> results = score.search("pizza", country="IT", nace="56.10", limit=5)
            >>> print(f"Found {results.total} pizzerias in Italy")
        """
        params: dict = {"q": query, "limit": str(limit)}
        if country:
            params["country"] = country
        if nace:
            params["nace"] = nace
        if status:
            params["status"] = status

        resp = self._client.get("/api/score/search", params=params)
        resp.raise_for_status()
        return SearchResult.from_response(resp.json(), query)

    def lookup(self, company_id: str) -> Company:
        """Get detailed company data by ID or VAT number.

        Args:
            company_id: Company ID or VAT number

        Returns:
            Company with full details

        Example:
            >>> company = score.lookup("IT12345678901")
            >>> print(f"{company.name}: health score {company.health_score}/100")
        """
        resp = self._client.get("/api/score/lookup", params={"id": company_id})
        resp.raise_for_status()
        data = resp.json()
        company_data = data.get("company", data.get("result", data))
        return Company.from_dict(company_data)

    def report(
        self, company_id: str, report_type: str = "basic"
    ) -> ReportResult:
        """Generate a company health report.

        Args:
            company_id: Company ID
            report_type: "basic" (5 credits), "pro" (10), "enterprise" (20)

        Returns:
            ReportResult with download URL when ready
        """
        resp = self._client.post(
            "/api/score/report",
            json={"company_id": company_id, "type": report_type},
        )
        resp.raise_for_status()
        data = resp.json()
        return ReportResult(
            report_id=data.get("report_id", ""),
            company_id=company_id,
            type=report_type,
            status=data.get("status", "processing"),
            download_url=data.get("download_url"),
            raw=data,
        )

    def credits(self) -> dict:
        """Check remaining API credits.

        Returns:
            Dict with plan, credits_remaining, credits_used, reset_date
        """
        resp = self._client.get("/api/score/credits")
        resp.raise_for_status()
        return resp.json()

    def stats(self) -> dict:
        """Get database statistics.

        Returns:
            Dict with total_companies, countries, last_updated, etc.
        """
        resp = self._client.get("/api/score/stats")
        resp.raise_for_status()
        return resp.json()

    def countries(self) -> list[dict]:
        """List available countries with company counts.

        Returns:
            List of dicts with country_code, country_name, company_count
        """
        resp = self._client.get("/api/score/countries")
        resp.raise_for_status()
        data = resp.json()
        return data.get("countries", data.get("data", []))

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

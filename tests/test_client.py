"""Prove dell'SDK, senza rete e senza chiave.

Il client accetta un `transport`: si passa un httpx.MockTransport e ogni
richiesta finisce in una funzione che decide la risposta. Cosi si copre anche
cio che rompe in silenzio — i fallback sul nome del campo — che altrimenti si
scoprono solo quando un utente riceve un elenco vuoto invece di un errore.
"""

from __future__ import annotations

import httpx
import pytest

from scala_score.client import Company, ScalaScore, SearchResult


def client(gestore, **kw) -> ScalaScore:
    """Un client le cui richieste vanno a `gestore` invece che in rete."""
    return ScalaScore("chiave", transport=httpx.MockTransport(gestore), **kw)


def rispondi(corpo, stato: int = 200):
    """Gestore che risponde sempre allo stesso modo e registra le richieste."""
    viste: list[httpx.Request] = []

    def gestore(request: httpx.Request) -> httpx.Response:
        viste.append(request)
        return httpx.Response(stato, json=corpo)

    gestore.viste = viste  # type: ignore[attr-defined]
    return gestore


# ─────────────────────────── costruttore ───────────────────────────

def test_base_url_predefinito():
    g = rispondi({})
    with client(g) as s:
        s.stats()
    assert str(g.viste[0].url) == "https://app.get-scala.com/api/score/stats"


def test_toglie_la_barra_finale():
    g = rispondi({})
    with client(g, base_url="https://esempio.test/") as s:
        s.stats()
    assert str(g.viste[0].url) == "https://esempio.test/api/score/stats"


def test_la_chiave_va_nell_intestazione_non_nell_url():
    g = rispondi({})
    with client(g) as s:
        s.stats()
    assert g.viste[0].headers["X-API-Key"] == "chiave"
    assert "chiave" not in str(g.viste[0].url)


def test_il_client_si_chiude_uscendo_dal_with():
    g = rispondi({})
    with client(g) as s:
        s.stats()
    assert s._client.is_closed


# ─────────────────────────── errori ───────────────────────────

@pytest.mark.parametrize("stato", [400, 401, 429, 500])
def test_uno_stato_di_errore_solleva(stato):
    with client(rispondi({"error": "no"}, stato)) as s:
        with pytest.raises(httpx.HTTPStatusError):
            s.stats()


# ─────────────────────────── Company.from_dict ───────────────────────────

def test_i_campi_diretti():
    c = Company.from_dict({"id": "1", "name": "Ferrero", "country": "IT", "city": "Alba"})
    assert (c.id, c.name, c.country, c.city) == ("1", "Ferrero", "IT", "Alba")


@pytest.mark.parametrize(
    "alternativo,atteso,campo",
    [
        ({"company_name": "Ferrero"}, "Ferrero", "name"),
        ({"country_code": "IT"}, "IT", "country"),
        ({"tax_id": "IT123"}, "IT123", "vat_number"),
        ({"street": "Via Roma 1"}, "Via Roma 1", "address"),
        ({"zip": "12051"}, "12051", "postal_code"),
        ({"nace": "10.71"}, "10.71", "nace_code"),
        ({"estimated_revenue": 100.0}, 100.0, "revenue"),
        ({"employee_count": 7}, 7, "employees"),
        ({"score": 88.0}, 88.0, "health_score"),
        ({"incorporation_date": "1946"}, "1946", "founded"),
    ],
)
def test_accetta_i_nomi_alternativi(alternativo, atteso, campo):
    """Ogni campo ha un secondo nome perche l'API li ha cambiati nel tempo."""
    assert getattr(Company.from_dict(alternativo), campo) == atteso


def test_il_nome_diretto_vince_sull_alternativo():
    c = Company.from_dict({"name": "giusto", "company_name": "vecchio"})
    assert c.name == "giusto"


def test_i_campi_assenti_diventano_stringa_vuota_o_none():
    c = Company.from_dict({})
    assert c.id == "" and c.name == "" and c.country == ""
    assert c.city is None and c.revenue is None


def test_raw_conserva_la_risposta_intera():
    grezzo = {"id": "1", "campo_che_non_conosciamo": 42}
    assert Company.from_dict(grezzo).raw == grezzo


# ─────────────────────────── search ───────────────────────────

def test_search_chiede_dieci_risultati_se_non_specificato():
    g = rispondi({"results": []})
    with client(g) as s:
        s.search("Ferrero")
    assert g.viste[0].url.params["q"] == "Ferrero"
    assert g.viste[0].url.params["limit"] == "10"


def test_search_passa_i_filtri_quando_ci_sono():
    g = rispondi({"results": []})
    with client(g) as s:
        s.search("x", country="IT", nace="56.10", status="active", limit=5)
    p = g.viste[0].url.params
    assert p["country"] == "IT" and p["nace"] == "56.10"
    assert p["status"] == "active" and p["limit"] == "5"


def test_search_non_manda_i_filtri_non_passati():
    g = rispondi({"results": []})
    with client(g) as s:
        s.search("x")
    p = g.viste[0].url.params
    assert "country" not in p and "nace" not in p and "status" not in p


@pytest.mark.parametrize("campo", ["results", "companies", "data"])
def test_search_legge_le_aziende_dai_tre_nomi(campo):
    with client(rispondi({campo: [{"id": "1", "name": "A"}]})) as s:
        r = s.search("x")
    assert len(r.companies) == 1 and r.companies[0].name == "A"


def test_search_senza_nessuno_dei_tre_campi_torna_vuoto():
    with client(rispondi({"altro": 1})) as s:
        r = s.search("x")
    assert r.companies == [] and r.total == 0


def test_search_usa_total_quando_c_e():
    with client(rispondi({"results": [{"id": "1"}], "total": 4321})) as s:
        assert s.search("x").total == 4321


def test_search_ripiega_sul_numero_di_aziende_ricevute():
    with client(rispondi({"results": [{"id": "1"}, {"id": "2"}]})) as s:
        assert s.search("x").total == 2


def test_search_crediti_valgono_uno_se_non_dichiarati():
    with client(rispondi({"results": []})) as s:
        assert s.search("x").credits_used == 1


def test_search_rispetta_i_crediti_dichiarati_anche_a_zero():
    with client(rispondi({"results": [], "credits_used": 0})) as s:
        assert s.search("x").credits_used == 0


def test_search_riporta_la_query_nel_risultato():
    with client(rispondi({"results": []})) as s:
        assert s.search("Ferrero").query == "Ferrero"


def test_from_response_e_usabile_da_sola():
    r = SearchResult.from_response({"results": [{"id": "1"}]}, "q")
    assert r.query == "q" and len(r.companies) == 1


# ─────────────────────────── lookup ───────────────────────────

def test_lookup_passa_id_come_parametro():
    g = rispondi({"company": {"id": "IT1", "name": "A"}})
    with client(g) as s:
        s.lookup("IT1")
    assert g.viste[0].url.path == "/api/score/lookup"
    assert g.viste[0].url.params["id"] == "IT1"


@pytest.mark.parametrize("campo", ["company", "result"])
def test_lookup_legge_dai_due_involucri(campo):
    with client(rispondi({campo: {"id": "1", "name": "A"}})) as s:
        assert s.lookup("1").name == "A"


def test_lookup_accetta_la_risposta_non_incartata():
    with client(rispondi({"id": "1", "name": "A"})) as s:
        assert s.lookup("1").name == "A"


# ─────────────────────────── report ───────────────────────────

def test_report_e_una_post_con_il_corpo():
    import json
    g = rispondi({"report_id": "r", "status": "queued"})
    with client(g) as s:
        s.report("1")
    assert g.viste[0].method == "POST"
    assert json.loads(g.viste[0].content) == {"company_id": "1", "type": "basic"}


@pytest.mark.parametrize("tipo", ["basic", "pro", "enterprise"])
def test_report_accetta_i_tre_tipi(tipo):
    import json
    g = rispondi({})
    with client(g) as s:
        s.report("1", tipo)
    assert json.loads(g.viste[0].content)["type"] == tipo


def test_report_riporta_i_campi_e_lo_stato_predefinito():
    with client(rispondi({"report_id": "r7", "download_url": "https://x/y"})) as s:
        r = s.report("c1", "pro")
    assert r.report_id == "r7"
    assert r.company_id == "c1"      # viene dall'argomento, non dalla risposta
    assert r.type == "pro"           # idem
    assert r.status == "processing"  # predefinito quando la risposta tace
    assert r.download_url == "https://x/y"


# ─────────────────────────── credits, stats, countries ───────────────────────────

def test_credits_restituisce_la_risposta_intera():
    corpo = {"plan": "pro", "credits_remaining": 900, "credits_used": 100, "reset_date": "2026-09-01"}
    with client(rispondi(corpo)) as s:
        assert s.credits() == corpo


def test_stats_restituisce_la_risposta_intera():
    corpo = {"total_companies": 244_000_000, "countries": 42, "last_updated": "2026-08-01"}
    with client(rispondi(corpo)) as s:
        assert s.stats() == corpo


@pytest.mark.parametrize("campo", ["countries", "data"])
def test_countries_legge_dai_due_nomi(campo):
    with client(rispondi({campo: [{"country_code": "IT", "company_count": 6}]})) as s:
        assert s.countries()[0]["country_code"] == "IT"


def test_countries_senza_nessuno_dei_due_torna_vuoto():
    with client(rispondi({})) as s:
        assert s.countries() == []


def test_close_chiude_anche_senza_with():
    s = client(rispondi({}))
    s.stats()
    s.close()
    assert s._client.is_closed

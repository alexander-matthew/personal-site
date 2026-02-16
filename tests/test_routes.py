"""Smoke tests for all page routes — verify they return 200."""
import pytest


class TestPageRoutes:
    """Every page route should return 200 OK."""

    @pytest.mark.parametrize("path", [
        "/",
        "/about",
        "/projects",
        "/blog/",
        "/news/",
        "/resume/",
        "/projects/spotify/",
        "/projects/blackjack/",
        "/projects/sudoku/",
        "/projects/pr-review/",
        "/projects/weather/",
        "/tools/",
    ])
    def test_page_returns_200(self, client, path):
        resp = client.get(path)
        assert resp.status_code == 200, f"{path} returned {resp.status_code}"

    def test_404_page(self, client):
        resp = client.get("/nonexistent-page-xyz")
        assert resp.status_code == 404

    def test_404_page_is_html(self, client):
        resp = client.get("/nonexistent-page-xyz")
        assert "text/html" in resp.headers.get("content-type", "")


class TestApiEndpoints:
    """Basic API endpoint tests (no auth required for weather)."""

    def test_weather_geocode_requires_city(self, client):
        resp = client.get("/projects/weather/api/geocode")
        assert resp.status_code == 422  # FastAPI validation error

    def test_weather_current_requires_params(self, client):
        resp = client.get("/projects/weather/api/current")
        assert resp.status_code == 422

    def test_weather_current_validates_coords(self, client):
        resp = client.get("/projects/weather/api/current?lat=abc&lon=def")
        assert resp.status_code == 422

    def test_weather_current_validates_range(self, client):
        resp = client.get("/projects/weather/api/current?lat=999&lon=999")
        assert resp.status_code == 422

    def test_weather_forecast_requires_params(self, client):
        resp = client.get("/projects/weather/api/forecast")
        assert resp.status_code == 422

    def test_weather_extremes_validates_horizon(self, client):
        resp = client.get("/projects/weather/api/extremes/invalid")
        assert resp.status_code == 422

    def test_weather_industry_returns_data(self, client):
        resp = client.get("/projects/weather/api/industry/florida")
        assert resp.status_code == 200
        data = resp.json()
        assert "industries" in data

    def test_weather_industry_404_for_unknown(self, client):
        resp = client.get("/projects/weather/api/industry/narnia")
        assert resp.status_code == 404

    def test_spotify_api_requires_auth(self, client):
        resp = client.get("/projects/spotify/api/recent")
        assert resp.status_code == 401


class TestSecurityHeaders:
    """Verify security headers are present on responses."""

    def test_security_headers_present(self, client):
        resp = client.get("/")
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_security_headers_on_api(self, client):
        resp = client.get("/projects/weather/api/industry/florida")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    def test_security_headers_on_404(self, client):
        resp = client.get("/nonexistent-page")
        assert resp.headers.get("x-frame-options") == "DENY"

    def test_csp_header_present(self, client):
        resp = client.get("/")
        csp = resp.headers.get("content-security-policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

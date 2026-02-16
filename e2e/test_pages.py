"""E2E tests for core page rendering using Playwright."""
import re

from playwright.sync_api import Page, expect


class TestHomePage:

    def test_home_loads_with_desktop_icons(self, page: Page, base_url: str):
        page.goto(base_url)
        expect(page).to_have_title(re.compile("Alexander"))
        # Win98 desktop should have clickable icons
        icons = page.locator(".win98-icon")
        expect(icons.first).to_be_visible()


class TestNavigation:

    def test_navigate_to_about(self, page: Page, base_url: str):
        page.goto(base_url + "/about")
        expect(page).to_have_title(re.compile("System Properties"))
        # Win98 window chrome should be visible
        expect(page.locator(".win98-title-bar")).to_be_visible()

    def test_navigate_to_projects(self, page: Page, base_url: str):
        page.goto(base_url + "/projects")
        expect(page).to_have_title(re.compile("Projects"))


class TestSpotifyAuth:

    def test_spotify_shows_auth_prompt(self, page: Page, base_url: str):
        page.goto(base_url + "/projects/spotify/")
        # Should show either "not configured" or "connect" box since we're unauthenticated
        auth_box = page.locator(".auth-box")
        expect(auth_box).to_be_visible()


class TestWeatherPage:

    def test_weather_loads_with_window(self, page: Page, base_url: str):
        page.goto(base_url + "/projects/weather/")
        expect(page).to_have_title(re.compile("Weather"))
        expect(page.locator(".win98-title-bar")).to_be_visible()


class Test404:

    def test_404_renders_for_unknown_route(self, page: Page, base_url: str):
        response = page.goto(base_url + "/this-page-does-not-exist")
        assert response.status == 404

"""E2E tests for core page rendering using Playwright."""
import re
from pathlib import Path

from playwright.sync_api import Page, expect

SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"


class TestHomePage:

    def test_home_loads_with_project_cards(self, page: Page, base_url: str):
        page.goto(base_url)
        expect(page).to_have_title(re.compile("Alexander"))
        # Should have project cards on the home page
        cards = page.locator(".project-card")
        expect(cards.first).to_be_visible()


class TestNavigation:

    def test_navigate_to_about(self, page: Page, base_url: str):
        page.goto(base_url + "/about")
        expect(page).to_have_title(re.compile("About"))

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

    def test_weather_loads(self, page: Page, base_url: str):
        page.goto(base_url + "/projects/weather/")
        expect(page).to_have_title(re.compile("Weather"))


class TestBlackjackPage:

    def test_blackjack_loads_with_felt(self, page: Page, base_url: str):
        page.goto(base_url + "/projects/blackjack/")
        expect(page).to_have_title(re.compile("Blackjack"))
        # Felt should be visible
        expect(page.locator(".bj-felt")).to_be_visible()
        # Chips should be visible on the felt
        expect(page.locator(".bj-felt-chip").first).to_be_visible()
        # Action bar should be hidden initially
        expect(page.locator("#action-bar")).to_have_class(re.compile("hidden"))

    def test_blackjack_place_bet_and_deal(self, page: Page, base_url: str):
        page.goto(base_url + "/projects/blackjack/")
        # Place a bet by clicking the $5 chip
        page.locator(".bj-felt-chip[data-value='5']").click()
        # Deal button should now be enabled
        deal_btn = page.locator("#deal-btn")
        expect(deal_btn).to_be_enabled()
        # Click deal
        deal_btn.click()
        # Cards should appear
        expect(page.locator("#dealer-cards .card").first).to_be_visible()
        # Action bar should now be visible
        expect(page.locator("#action-bar")).not_to_have_class(re.compile("hidden"))

    def test_blackjack_solitaire_visual(self, page: Page, base_url: str):
        page.goto(base_url + "/projects/blackjack/")
        page.wait_for_load_state("networkidle")
        SCREENSHOTS_DIR.mkdir(exist_ok=True)
        page.screenshot(path=str(SCREENSHOTS_DIR / "blackjack_betting.png"))


class Test404:

    def test_404_renders_for_unknown_route(self, page: Page, base_url: str):
        response = page.goto(base_url + "/this-page-does-not-exist")
        assert response.status == 404

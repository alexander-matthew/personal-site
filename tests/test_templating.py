"""Tests for app/templating.py."""


class TestUrlFor:
    """Test the Flask-compatible url_for function."""

    def test_static_file_url(self, app):
        from app.templating import templates
        url_for = templates.env.globals['url_for']
        assert url_for('static', filename='css/style.css') == '/static/css/style.css'

    def test_named_route(self, app):
        from app.templating import templates
        url_for = templates.env.globals['url_for']
        assert url_for('main.home') == '/'

    def test_route_with_params(self, app):
        from app.templating import templates
        url_for = templates.env.globals['url_for']
        url = url_for('blog.post', slug='test-post')
        assert url == '/blog/test-post'

    def test_unknown_route_returns_fallback(self, app):
        from app.templating import templates
        url_for = templates.env.globals['url_for']
        assert url_for('nonexistent.route') == '#'

    def test_site_config_available(self, app):
        from app.templating import templates
        site = templates.env.globals['site']
        assert site['name'] == 'Alexander'
        assert 'github_url' in site
        assert 'linkedin_url' in site

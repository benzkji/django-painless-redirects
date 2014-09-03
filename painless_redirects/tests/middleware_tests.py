"""Tests for the models of the painless_redirects app."""
from django.http import QueryDict
from django.test import TestCase
from mock import Mock

from . import factories
from ..middleware import ManualRedirectMiddleware, ForceSiteDomainRedirectMiddleware


class ForceSiteDomainRedirectMiddlewareTestCase(TestCase):

    def setUp(self):
        self.middleware = ForceSiteDomainRedirectMiddleware()
        self.request = Mock()
        self.request.is_secure = lambda: False
        self.request.get_host = lambda: "nogood.com"
        self.request.GET = QueryDict("")
        self.request.path = "/"

    def test_no_redirect(self):
        self.request.get_host = lambda: "example.com"
        response = self.middleware.process_request(self.request)
        self.assertEqual(response, None)

    def test_debug_no_redirect(self):
        with self.settings(DEBUG=True):
            response = self.middleware.process_request(self.request)
            self.assertEqual(response, None)

    def test_must_redirect(self):
        response = self.middleware.process_request(self.request)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "http://example.com/")

    def test_must_redirect_preserves_path(self):
        self.request.path = "/abc/def/yeah/"
        response = self.middleware.process_request(self.request)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "http://example.com/abc/def/yeah/")

    def test_must_redirect_preserves_getvars(self):
        self.request.path = "/abc/def/yeah/"
        self.request.GET = QueryDict("karma=true&param=value")
        response = self.middleware.process_request(self.request)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "http://example.com/abc/def/yeah/?karma=true&param=value")


class ManualRedirectMiddlewareTestCase(TestCase):
    """
    request.get_current_site() is always the default example.com fixture
    check: http://blog.namis.me/2012/05/13/writing-unit-tests-for-django-middleware/
    """
    def setUp(self):
        self.middleware = ManualRedirectMiddleware()
        self.request = Mock()
        self.response = Mock()

    def test_no_404(self):
        obj = factories.RedirectFactory()
        self.request.path = obj.old_path
        self.response.status_code = 200
        self.assertEqual(
            self.middleware.process_response(self.request, self.response),
            self.response)

    def test_no_redirect_found(self):
        factories.RedirectFactory()
        self.request.path = "/some-other-path/"
        self.response.status_code = 404
        self.assertEqual(
            self.middleware.process_response(self.request, self.response),
            self.response)

    def test_simple_redirect(self):
        obj = factories.RedirectFactory()
        self.response.status_code = 404
        self.request.path = obj.old_path
        response = self.middleware.process_response(self.request, self.response)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "/the-new-path/")

    def test_new_site_redirect(self):
        obj = factories.RedirectFactory()
        obj.new_site = factories.SiteFactory()
        obj.save()
        self.response.status_code = 404
        self.request.path = "/the-old-path/"
        response = self.middleware.process_response(self.request, self.response)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response.url, "%s%s" % (obj.new_site.domain, obj.new_path))
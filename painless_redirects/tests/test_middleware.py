# coding: utf-8
from __future__ import unicode_literals

from django.contrib.sites.models import Site
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
        self.request.META = {}
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
        self.request.GET = QueryDict("karma=true")
        response = self.middleware.process_request(self.request)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "http://example.com/abc/def/yeah/?karma=true")


class ManualRedirectMiddlewareTestCase(TestCase):
    """
    request.get_current_site() is always the default example.com fixture
    check: http://blog.namis.me/2012/05/13/writing-unit-tests-for-django-middleware/
    """
    def setUp(self):
        self.middleware = ManualRedirectMiddleware()
        self.request = Mock()
        self.request.META = {}
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

    def test_no_redirect_when_site_specified(self):
        obj = factories.RedirectFactory()
        obj.site = factories.SiteFactory()
        obj.save()
        self.request.path = obj.old_path
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

    # TODO: could not yet reproduce this problem with a test!
    def test_redirect_special_chars_get_var(self):
        obj = factories.RedirectFactory()
        self.response.status_code = 404
        self.request.path = obj.old_path
        self.request.META = {}
        # self.request.META['QUERY_STRING'] = 'special=charséàè)(/&%çç*"næßđð“½&amp;what=the;:_éà£Pè!'
        # self.request.META['QUERY_STRING'] = 'lang=de&s=poste\xc3\x83\xc6\x92\xc3\xa2\xe2\x82\xac\xc5\xa1\xc3\x83\xe2\x80\x9a\xc3\x82\xc2\xa8'
        response = self.middleware.process_response(self.request, self.response)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "/the-new-path/")

    # TODO: this is not what works! one should add http(s)://
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

    def test_wildcard_redirect(self):
        obj = factories.RedirectFactory()
        obj.old_path = "/the-wildcard/yes/"
        obj.wildcard_match = True
        obj.save()
        self.response.status_code = 404
        self.request.path = "%sthe/right/part/" % obj.old_path
        response = self.middleware.process_response(self.request, self.response)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "/the-new-path/")

    def test_wildcard_redirect_with_site(self):
        obj = factories.RedirectFactory()
        obj.site = Site.objects.get_current()
        obj.old_path = "/the-wildcard/yes/"
        obj.wildcard_match = True
        obj.save()
        self.response.status_code = 404
        self.request.path = "%sthe/right/part/" % obj.old_path
        response = self.middleware.process_response(self.request, self.response)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "/the-new-path/")

    def test_redirect_without_slash(self):
        obj = factories.RedirectFactory()
        obj.old_path = '/whatever/check.html'
        obj.save()
        self.request.path = obj.old_path
        self.response.status_code = 404
        response = self.middleware.process_response(self.request, self.response)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "/the-new-path/")

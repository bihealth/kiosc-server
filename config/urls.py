from django.conf import settings
from django.conf.urls import include
from django.urls import path
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views import defaults as default_views
from django.views.generic import TemplateView

from projectroles.views import HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),
    # Admin URLs - most occur before Django Admin, otherwise urls will be matched by that.
    path("kioscadmin/", include("kioscadmin.urls")),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # Login and logout
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="users/login.html"),
        name="login",
    ),
    path("logout/", auth_views.logout_then_login, name="logout"),
    # Auth
    path("api/auth/", include("knox.urls")),
    # Social auth for OIDC support
    path("social/", include("social_django.urls")),
    # Projectroles URLs
    path("project/", include("projectroles.urls")),
    # Timeline URLs
    path("timeline/", include("timeline.urls")),
    # django-db-file-storage URLs (obfuscated for users)
    # TODO: Change the URL to something obfuscated (e.g. random string)
    path("CHANGE-ME/", include("db_file_storage.urls")),
    # Background Jobs URLs
    path("bgjobs/", include("bgjobs.urls")),
    # Data Cache app
    # path(r'^cache/', include('sodarcache.urls')),
    # User Profile URLs
    path("user/", include("userprofile.urls")),
    # Admin Alerts URLs
    path("adminalerts/", include("adminalerts.urls")),
    # App Alerts URLs
    path("appalerts/", include("appalerts.urls")),
    # Site Info URLs
    path("siteinfo/", include("siteinfo.urls")),
    # API Tokens URLs
    path("tokens/", include("tokens.urls")),
    # Containers URLs
    path("containers/", include("containers.urls")),
    # Containertemplates URLs
    path("containertemplates/", include("containertemplates.urls")),
    # Iconify icon URLs
    path("icons/", include("dj_iconify.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.KIOSC_EMBEDDED_FILES:
    urlpatterns.append(path("files/", include("filesfolders.urls")))

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]

    urlpatterns += staticfiles_urlpatterns()

    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls))
        ] + urlpatterns

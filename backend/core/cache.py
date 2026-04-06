import functools
import hashlib
import logging
import uuid

from django.core.cache import cache
from rest_framework.response import Response

from core.constants import CACHE_TTL_VERSION

logger = logging.getLogger(__name__)


def _make_key(prefix, *args):
    """Build a deterministic cache key from prefix and arguments."""
    raw = ":".join(str(a) for a in args)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"vt:{prefix}:{digest}"


def _get_project_version(project_id):
    """Get the current version counter for a project's cache."""
    ver_key = _make_key("project_ver", str(project_id))
    version = cache.get(ver_key)
    if version is None:
        version = str(uuid.uuid4())
        # Use a long TTL so the version key outlives cached data
        cache.set(ver_key, version, timeout=CACHE_TTL_VERSION)
    return version


def cached_view(key_prefix, timeout=60, vary_on_query=None, project_kwarg="project_slug"):
    """Decorator for caching view responses."""
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            project_slug = kwargs.get(project_kwarg, "")
            project_version = ""
            if project_slug:
                project_version = _get_project_version(project_slug)

            key_parts = [key_prefix, request.user.pk, project_version]
            key_parts.extend(str(v) for v in kwargs.values())
            if vary_on_query:
                for param in sorted(vary_on_query):
                    val = request.query_params.get(param, "")
                    key_parts.append(f"{param}={val}")

            page = request.query_params.get("page", "1")
            key_parts.append(f"p={page}")

            cache_key = _make_key(*key_parts)

            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return Response(cached_data)

            response = view_func(request, *args, **kwargs)
            # Only cache successful responses
            if response.status_code == 200:
                cache.set(cache_key, response.data, timeout)
            return response
        return wrapper
    return decorator


def invalidate_project_cache(project_id, project_slug=None):
    """Invalidate all cached data for a project.

    Both the ID-based and slug-based version keys are updated so that
    views using either key (detail views use ID, list views use slug)
    see the invalidation.
    """
    new_version = str(uuid.uuid4())

    ver_key_id = _make_key("project_ver", str(project_id))
    cache.set(ver_key_id, new_version, timeout=CACHE_TTL_VERSION)

    if project_slug:
        ver_key_slug = _make_key("project_ver", str(project_slug))
        cache.set(ver_key_slug, new_version, timeout=CACHE_TTL_VERSION)
    else:
        # Always try to look up the slug so invalidation is complete
        from projects.models import Project  # noqa: avoid circular import at module level
        try:
            slug = Project.objects.filter(id=project_id).values_list("slug", flat=True).first()
            if slug:
                ver_key_slug = _make_key("project_ver", str(slug))
                cache.set(ver_key_slug, new_version, timeout=CACHE_TTL_VERSION)
        except Exception:
            logger.debug("Could not look up slug for project %s during cache invalidation", project_id)

    logger.debug(
        "Invalidated cache for project %s (slug=%s, new version %s)",
        project_id, project_slug, new_version,
    )

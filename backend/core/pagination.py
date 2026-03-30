"""
Reusable pagination helper for function-based DRF views.

DRF's DEFAULT_PAGINATION_CLASS only applies to generic views and viewsets.
Function-based views using @api_view must paginate manually. This module
provides a ``paginate_queryset`` helper that produces the same envelope
format as ``rest_framework.pagination.PageNumberPagination``.

Usage::

    from core.pagination import paginate_queryset

    @api_view(["GET"])
    def my_list_view(request):
        qs = MyModel.objects.all()
        return paginate_queryset(qs, request, MySerializer)
"""

from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

__all__ = ["paginate_queryset", "paginate_list", "StandardPagination"]


class StandardPagination(PageNumberPagination):
    """Concrete paginator that honours ``settings.REST_FRAMEWORK["PAGE_SIZE"]``."""

    page_size = getattr(settings, "REST_FRAMEWORK", {}).get("PAGE_SIZE", 25)
    page_size_query_param = "page_size"
    max_page_size = 100


def paginate_queryset(queryset, request, serializer_class, page_size=None, context=None):
    """Paginate *queryset* and return a :class:`Response` in DRF standard format.

    Parameters
    ----------
    queryset : QuerySet
        The (already-filtered / ordered) queryset to paginate.
    request : Request
        The DRF request object (needed for building next/previous links).
    serializer_class : Serializer
        The DRF serializer to use for the results.
    page_size : int, optional
        Override the default page size for this call.
    context : dict, optional
        Extra context to pass to the serializer.

    Returns
    -------
    Response
        ``{"count": N, "next": url|null, "previous": url|null, "results": [...]}``
    """
    paginator = StandardPagination()
    if page_size is not None:
        paginator.page_size = page_size

    page = paginator.paginate_queryset(queryset, request)
    if page is not None:
        serializer_context = {"request": request}
        if context:
            serializer_context.update(context)
        serializer = serializer_class(page, many=True, context=serializer_context)
        return paginator.get_paginated_response(serializer.data)

    # Fallback: if the paginator returns None (shouldn't happen with PageNumber)
    serializer = serializer_class(queryset, many=True, context={"request": request})
    return Response(serializer.data)


def paginate_list(data_list, request, page_size=None):
    """Paginate a plain Python list (not a queryset) and return a Response.

    Useful for views that build result lists manually (e.g. overview_rules).

    Parameters
    ----------
    data_list : list
        The pre-built list of dicts/objects.
    request : Request
        The DRF request object.
    page_size : int, optional
        Override the default page size.

    Returns
    -------
    Response
        Standard DRF pagination envelope.
    """
    paginator = StandardPagination()
    if page_size is not None:
        paginator.page_size = page_size

    page = paginator.paginate_queryset(data_list, request)
    if page is not None:
        return paginator.get_paginated_response(page)

    return Response(data_list)

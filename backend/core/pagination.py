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
    """Paginate *queryset* and return a :class:`Response` in DRF standard format."""
    
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

    serializer = serializer_class(queryset, many=True, context={"request": request})
    return Response(serializer.data)


def paginate_list(data_list, request, page_size=None):
    """Paginate a plain Python list (not a queryset) and return a Response."""

    paginator = StandardPagination()
    if page_size is not None:
        paginator.page_size = page_size

    page = paginator.paginate_queryset(data_list, request)
    if page is not None:
        return paginator.get_paginated_response(page)

    return Response(data_list)

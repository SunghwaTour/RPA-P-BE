from rest_framework.pagination import PageNumberPagination

class Pagination(PageNumberPagination):
    page_size = 10  # 기본 페이지 크기
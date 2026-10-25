# Django Admin chỉ để xem nhanh (dữ liệu được nạp lại bằng load_to_postgres.py).
# Các bảng khóa ghép (observation, forecast, ...) chưa được Django Admin 5.2 hỗ trợ; xem chúng bằng pgAdmin.
from django.contrib import admin

from .models import AppMeta, District, GridCell


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(District)
class DistrictAdmin(ReadOnlyAdmin):
    list_display = ('district_id', 'name_vi', 'n_cells')


@admin.register(GridCell)
class GridCellAdmin(ReadOnlyAdmin):
    list_display = ('cell_id', 'district', 'lon', 'lat')
    list_filter = ('district',)
    search_fields = ('cell_id',)


@admin.register(AppMeta)
class AppMetaAdmin(ReadOnlyAdmin):
    list_display = ('key',)

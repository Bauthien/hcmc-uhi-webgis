# models.py - ánh xạ các bảng do postgres/schema.sql tạo ra.
# managed = False: Django chỉ đọc, không tạo hay xóa các bảng này (load_to_postgres.py quản lý).
# Cột hình học (geom) không khai báo ở đây; PostGIS xử lý và API lấy GeoJSON bằng SQL (ST_AsGeoJSON).
from django.db import models


class District(models.Model):
    district_id = models.AutoField(primary_key=True)
    name_vi = models.TextField(unique=True)
    n_cells = models.IntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'district'
        ordering = ['name_vi']
        verbose_name = 'quận/huyện'
        verbose_name_plural = 'quận/huyện'

    def __str__(self):
        return self.name_vi


class GridCell(models.Model):
    cell_id = models.TextField(primary_key=True)
    district = models.ForeignKey(District, models.DO_NOTHING, db_column='district_id')
    lon = models.FloatField()
    lat = models.FloatField()

    class Meta:
        managed = False
        db_table = 'grid_cell'
        verbose_name = 'ô lưới 1 km'
        verbose_name_plural = 'ô lưới 1 km'

    def __str__(self):
        return self.cell_id


class Observation(models.Model):
    pk = models.CompositePrimaryKey('cell', 'obs_month')
    cell = models.ForeignKey(GridCell, models.DO_NOTHING, db_column='cell_id')
    obs_month = models.DateField()
    lst = models.FloatField(null=True)
    ndvi = models.FloatField(null=True)
    tvdi = models.FloatField(null=True)
    utfvi = models.FloatField(null=True)
    utfvi_class = models.SmallIntegerField(null=True)
    no2 = models.FloatField(null=True)
    co = models.FloatField(null=True)
    aod = models.FloatField(null=True)
    observed = models.BooleanField(null=True)

    class Meta:
        managed = False
        db_table = 'observation'


class Forecast(models.Model):
    pk = models.CompositePrimaryKey('cell', 'indicator', 'target_month')
    cell = models.ForeignKey(GridCell, models.DO_NOTHING, db_column='cell_id')
    indicator = models.TextField()
    target_month = models.DateField()
    horizon = models.SmallIntegerField()
    forecast = models.FloatField(null=True)
    lower = models.FloatField(null=True)
    upper = models.FloatField(null=True)
    climatology = models.FloatField(null=True)
    utfvi_class = models.SmallIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'forecast'


class Validation2026(models.Model):
    pk = models.CompositePrimaryKey('cell', 'indicator', 'obs_month')
    cell = models.ForeignKey(GridCell, models.DO_NOTHING, db_column='cell_id')
    indicator = models.TextField()
    obs_month = models.DateField()
    actual = models.FloatField(null=True)
    forecast = models.FloatField(null=True)
    climatology = models.FloatField(null=True)

    class Meta:
        managed = False
        db_table = 'validation_2026'


class Reliability(models.Model):
    pk = models.CompositePrimaryKey('indicator', 'horizon')
    indicator = models.TextField()
    horizon = models.SmallIntegerField()
    rmse_model = models.FloatField(null=True)
    rmse_climatology = models.FloatField(null=True)
    vs_climatology_pct = models.FloatField(null=True)
    err_q10 = models.FloatField(null=True)
    err_q90 = models.FloatField(null=True)
    reliability = models.TextField(null=True)

    class Meta:
        managed = False
        db_table = 'reliability'


class AppMeta(models.Model):
    key = models.TextField(primary_key=True)
    value = models.JSONField(null=True)

    class Meta:
        managed = False
        db_table = 'app_meta'
        verbose_name = 'mô tả ứng dụng'
        verbose_name_plural = 'mô tả ứng dụng'

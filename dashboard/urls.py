from django.urls import path

from . import api, views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/health/', api.health),
    path('api/meta/', api.meta),
    path('api/cells/', api.cells),
    path('api/districts/', api.district_shapes),
    path('api/values/', api.values),
    path('api/series/', api.series),
    path('api/forecast/', api.forecast),
    path('api/validation/', api.validation),
    path('api/ranking/', api.ranking),
    path('api/locate/', api.locate),
]

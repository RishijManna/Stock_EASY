from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("medicines/", views.medicines, name="medicines"),
    path("medicine/<int:pk>/partial/", views.medicine_detail_partial, name="medicine_detail_partial"),
    path("medicine/<int:pk>/edit/partial/", views.medicine_edit_partial, name="medicine_edit_partial"),
    path("medicine/<int:pk>/edit/", views.medicine_edit, name="medicine_edit"),
    path("medicine/<int:pk>/delete/", views.medicine_delete, name="medicine_delete"),
    path("medlist/", views.medlist_partial, name="medlist_partial"),

    path("records/", views.records, name="records"),

    path("manufacturers/", views.manufacturers, name="manufacturers"),
    # ✅ add these two
    path("manufacturers/<int:pk>/edit/", views.manufacturer_edit, name="manufacturer_edit"),
    path("manufacturers/<int:pk>/delete/", views.manufacturer_delete, name="manufacturer_delete"),
]

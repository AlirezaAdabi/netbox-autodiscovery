from django.urls import path
from . import views

urlpatterns = [
    # Scanners
    path("scanners/", views.ScannerListView.as_view(), name="scanner_list"),
    path("scanners/add/", views.ScannerEditView.as_view(), name="scanner_add"),
    path("scanners/<int:pk>/", views.ScannerView.as_view(), name="scanner"),
    path("scanners/<int:pk>/edit/", views.ScannerEditView.as_view(), name="scanner_edit"),
    path("scanners/<int:pk>/delete/", views.ScannerDeleteView.as_view(), name="scanner_delete"),
    path("scanners/<int:pk>/run/", views.ScannerRunView.as_view(), name="scanner_run"),
    path(
    "scanners/<int:pk>/changelog/",
    views.ScannerChangeLogView.as_view(),
    name="scanner_changelog",
    ),
    path("scanners/delete/", views.ScannerBulkDeleteView.as_view(), name="scanner_bulk_delete"),

    # Runs
    path("runs/", views.ScanRunListView.as_view(), name="scanrun_list"),
    path("runs/<int:pk>/", views.ScanRunView.as_view(), name="scanrun"),
    path("runs/<int:pk>/edit/", views.ScanRunEditView.as_view(), name="scanrun_edit"),
    path("runs/<int:pk>/delete/", views.ScanRunDeleteView.as_view(), name="scanrun_delete"),
    path("runs/<int:pk>/changelog/", views.ScanRunChangeLogView.as_view(), name="scanrun_changelog"),
    path("runs/delete/", views.ScanRunBulkDeleteView.as_view(), name="scanrun_bulk_delete"),


]

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django_rq import enqueue
from netbox.views import generic
from .models import Scanner, ScanRun,ScanFinding
from .tables import ScannerTable, ScanRunTable,ScanFindingTable
from .forms import ScannerForm
from .tasks import run_scanner
# Scanner views
class ScannerListView(generic.ObjectListView):
    queryset = Scanner.objects.all()
    table = ScannerTable


class ScannerView(generic.ObjectView):
    queryset = Scanner.objects.all()
    template_name = "netbox_autodiscovery/scanner.html"


class ScannerEditView(generic.ObjectEditView):
    queryset = Scanner.objects.all()
    form = ScannerForm


class ScannerDeleteView(generic.ObjectDeleteView):
    queryset = Scanner.objects.all()
    



class ScanRunListView(generic.ObjectListView):
    queryset = ScanRun.objects.all()
    table = ScanRunTable

class ScanRunView(generic.ObjectView):
    queryset = ScanRun.objects.all()
    template_name = "netbox_autodiscovery/scanrun.html"

    def get_extra_context(self, request, instance):
        findings = ScanFinding.objects.filter(run=instance)
        table = ScanFindingTable(findings, orderable=False)
        return {"findings": table}


class ScannerRunView(generic.ObjectView):
    queryset = Scanner.objects.all()

    def get(self, request, pk):
        scanner = get_object_or_404(Scanner, pk=pk)

        run = ScanRun.objects.create(scanner=scanner)
        enqueue(run_scanner, run.id)

        messages.success(request, f"Started scan run {run.id} for {scanner.name}")
        return redirect("plugins:netbox_autodiscovery:scanrun", pk=run.id)
    
class ScannerBulkDeleteView(generic.BulkDeleteView):
    queryset = Scanner.objects.all()
    table = ScannerTable





class ScannerChangeLogView(generic.ObjectChangeLogView):
    queryset = Scanner.objects.all()
    


class ScanRunEditView(generic.ObjectEditView):
    queryset = ScanRun.objects.all()

class ScanRunDeleteView(generic.ObjectDeleteView):
    queryset = ScanRun.objects.all()

class ScanRunChangeLogView(generic.ObjectChangeLogView):
    queryset = ScanRun.objects.all()

class ScanRunBulkDeleteView(generic.BulkDeleteView):
    queryset = ScanRun.objects.all()
    table = ScanRunTable

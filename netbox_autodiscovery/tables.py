import django_tables2 as tables
from netbox.tables import NetBoxTable
from .models import Scanner, ScanRun,ScanFinding
from django.urls import reverse
from django.utils.html import format_html

class ScannerTable(NetBoxTable):
    pk = tables.CheckBoxColumn()  # ✅ bulk select checkbox
    name = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = Scanner
        fields = ("pk", "name", "type", "created")
        default_columns = ("name", "type", "created")


class ScanRunTable(NetBoxTable):
    pk = tables.CheckBoxColumn() 
    run = tables.Column(empty_values=(), verbose_name="Run")
    scanner = tables.Column(linkify=True)
    status = tables.Column()
    started = tables.Column()
    finished = tables.Column()

    class Meta(NetBoxTable.Meta):
        model = ScanRun
        fields = ("pk", "run","scanner", "status", "started", "finished")
        default_columns = ("run","scanner", "status", "started", "finished")
        exclude = ("actions",)
        
    def render_run(self, record):
        # 'record' is the ScanRun instance
        url = reverse("plugins:netbox_autodiscovery:scanrun", args=[record.pk])
        return format_html('<a href="{}">Run #{}</a>', url, record.pk)
    
    
class ScanFindingTable(tables.Table): 
    summary = tables.Column()
    details = tables.Column()

    class Meta:
        model = ScanFinding
        fields = ("summary", "details", "created")
        default_columns = ("summary", "details", "created")



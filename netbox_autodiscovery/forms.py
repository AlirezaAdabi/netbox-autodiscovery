# forms.py
from django import forms
from netbox.forms import NetBoxModelForm, NetBoxModelBulkEditForm
from .models import Scanner

class ScannerForm(NetBoxModelForm):
    cidr = forms.CharField(required=False, help_text="CIDR range (e.g. 192.168.1.0/24)")
    hostname = forms.CharField(required=False, help_text="Cisco switch hostname or IP")
    username = forms.CharField(required=False)
    password = forms.CharField(required=False, widget=forms.PasswordInput)
    community = forms.CharField(
        required=False,
        help_text="SNMP community string"
    )
    fake_mode = forms.BooleanField(required=False, help_text="Use fake discovery mode (for testing)")

    class Meta:
        model = Scanner
        fields = ("name", "type", "cidr", "hostname", "username", "password", "community","fake_mode")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.params:
            # pre-fill params
            self.fields["cidr"].initial = self.instance.params.get("cidr")
            self.fields["hostname"].initial = self.instance.params.get("hostname")
            self.fields["username"].initial = self.instance.params.get("username")
            self.fields["password"].initial = self.instance.params.get("password")
            self.fields["community"].initial = self.instance.params.get("community")
            self.fields["fake_mode"].initial = self.instance.params.get("fake_mode", False)

    def save(self, commit=True):
        obj = super().save(commit=False)

        if obj.type == Scanner.ScannerType.RANGE:
            obj.params = {
                "cidr": self.cleaned_data["cidr"],
                "fake_mode": self.cleaned_data["fake_mode"],
            }        
        elif obj.type == Scanner.ScannerType.CISCO:
            obj.params = {
                "hostname": self.cleaned_data["hostname"],
                "username": self.cleaned_data["username"],
                "password": self.cleaned_data["password"],
                "community": self.cleaned_data["community"],
                "fake_mode": self.cleaned_data["fake_mode"],

            }

        if commit:
            obj.save()
        return obj


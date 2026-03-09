from django import forms
from .models import PublicIP


class PublicIPForm(forms.ModelForm):
    class Meta:
        model = PublicIP
        fields = [
            "client",
            "pppoe_account",
            "status",
            "observacoes",
        ]
        widgets = {
            "client": forms.Select(attrs={
                "class": "form-control"
            }),
            "pppoe_account": forms.Select(attrs={
                "class": "form-control"
            }),
            "status": forms.Select(attrs={
                "class": "form-control"
            }),
            "observacoes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Digite observações sobre este IP"
            }),
        }
        
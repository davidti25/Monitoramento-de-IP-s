from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm


class AccessUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        label="Nome",
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Digite o nome do usuário"
        })
    )

    email = forms.EmailField(
        label="E-mail",
        required=False,
        widget=forms.EmailInput(attrs={
            "placeholder": "Digite o e-mail"
        })
    )

    group = forms.ModelChoiceField(
        label="Nível de acesso",
        queryset=Group.objects.all(),
        required=False,
        empty_label="Selecione o nível"
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "email",
            "password1",
            "password2",
            "group",
        ]
        widgets = {
            "username": forms.TextInput(attrs={
                "placeholder": "Digite o login"
            }),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get("first_name", "")
        user.email = self.cleaned_data.get("email", "")
        user.is_active = True

        if commit:
            user.save()

            group = self.cleaned_data.get("group")
            if group:
                user.groups.clear()
                user.groups.add(group)

        return user

class PublicIPForm(forms.ModelForm):
    client_name = forms.CharField(
        label="Cliente",
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Digite o nome do cliente"
        })
    )

    pppoe_username = forms.CharField(
        label="PPPoE",
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Digite o PPPoE"
        })
    )

    class Meta:
        model = PublicIP
        fields = [
            "status",
            "observacoes",
        ]
        widgets = {
            "status": forms.Select(),
            "observacoes": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Digite observações sobre este IP"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            if self.instance.client:
                self.fields["client_name"].initial = self.instance.client.nome

            if self.instance.pppoe_account:
                self.fields["pppoe_username"].initial = self.instance.pppoe_account.username

    def save(self, commit=True):
        instance = super().save(commit=False)

        client_name = self.cleaned_data.get("client_name", "").strip()
        pppoe_username = self.cleaned_data.get("pppoe_username", "").strip()

        pppoe_username = (
            pppoe_username
            .replace("PPPoE:", "")
            .replace("pppoe:", "")
            .strip()
        )

        client = None
        if client_name:
            client, _ = Client.objects.get_or_create(nome=client_name)

        pppoe = None
        if pppoe_username:
            pppoe, _ = PPPoEAccount.objects.get_or_create(username=pppoe_username)

            if client and pppoe.client_id != client.id:
                pppoe.client = client
                pppoe.save()

        if not client and pppoe and pppoe.client:
            client = pppoe.client

        instance.client = client
        instance.pppoe_account = pppoe

        if commit:
            instance.save()

        return instance
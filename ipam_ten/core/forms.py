from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group

from .models import Client, PPPoEAccount, PublicIP


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

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "email",
            "password1",
            "password2",
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

            grupo_consulta, _ = Group.objects.get_or_create(name="Consulta")
            user.groups.clear()
            user.groups.add(grupo_consulta)

        return user
     
class UserAccessUpdateForm(forms.ModelForm):
    group = forms.ModelChoiceField(
        label="Perfil de acesso",
        queryset=Group.objects.all(),
        required=False,
        empty_label="Selecione o perfil"
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "email",
            "is_active",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={
                "placeholder": "Nome do usuário"
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "E-mail"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            grupo_atual = self.instance.groups.first()
            if grupo_atual:
                self.fields["group"].initial = grupo_atual

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()

            grupo = self.cleaned_data.get("group")
            user.groups.clear()
            if grupo:
                user.groups.add(grupo)

        return user 
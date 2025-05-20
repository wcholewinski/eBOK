from django import forms
from django.contrib.auth.models import User
from .models import Apartment, Tenant, Payment


class ApartmentForm(forms.ModelForm):
    class Meta:
        model = Apartment
        fields = ['number', 'floor', 'area', 'rent', 'trash_fee', 'water_fee', 'gas_fee']

class TenantForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Tenant
        fields = ['apartment', 'num_occupants']

    def save(self, commit=True):
        # tworzymy usera i tenant razem
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )
        tenant = super().save(commit=False)
        tenant.user = user
        if commit:
            tenant.save()
        return tenant

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['tenant', 'date', 'amount', 'type', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label="Plik CSV z danymi mieszkań")

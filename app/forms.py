from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Apartment, Tenant, Payment, Ticket

# Formularz do dodawania/edycji mieszkań
class ApartmentForm(forms.ModelForm):
    class Meta:
        model = Apartment
        fields = ['number', 'floor', 'area', 'rent', 'trash_fee', 'water_fee', 'gas_fee']

# Formularz do rejestracji najemcy + przypisanie do mieszkania
class TenantForm(UserCreationForm):
    apartment = forms.ModelChoiceField(
        queryset=Apartment.objects.all(),
        label='Mieszkanie'
    )
    num_occupants = forms.IntegerField(
        min_value=1,
        label='Liczba osób'
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'apartment', 'num_occupants']

    def save(self, commit=True):
        # Tworzymy użytkownika
        user = super().save(commit)
        # Tworzymy powiązany obiekt Tenant
        Tenant.objects.create(
            user=user,
            apartment=self.cleaned_data['apartment'],
            num_occupants=self.cleaned_data['num_occupants']
        )
        return user

# Formularz płatności
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['tenant', 'date', 'amount', 'type', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

# Formularz importu CSV mieszkań
class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label="Plik CSV z danymi mieszkań",
        help_text="Format: number,floor,area,rent,trash_fee,water_fee,gas_fee"
    )

# Formularz zgłoszenia (ticket)
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'title': 'Tytuł zgłoszenia',
            'description': 'Opis',
            'status': 'Status'
        }
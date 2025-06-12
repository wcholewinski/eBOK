from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Apartment, Tenant, Payment, Ticket, BuildingAlert, MaintenanceRequest


# Formularze podstawowych modeli
class ApartmentForm(forms.ModelForm):
    class Meta:
        model = Apartment
        fields = ['number', 'floor', 'area', 'rent', 'trash_fee', 'water_fee', 'gas_fee']
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'floor': forms.NumberInput(attrs={'class': 'form-control'}),
            'area': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'rent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'trash_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'water_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'gas_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class TenantForm(forms.ModelForm):
    first_name = forms.CharField(required=True, label="Imię", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, label="Nazwisko", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    username = forms.CharField(required=True, label="Login", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Hasło")
    phone_number = forms.CharField(required=False, label="Numer telefonu", widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Tenant
        fields = ['apartment', 'num_occupants']
        widgets = {
            'apartment': forms.Select(attrs={'class': 'form-control'}),
            'num_occupants': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        # Tworzenie użytkownika
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        # Tworzenie najemcy
        tenant = super().save(commit=False)
        tenant.user = user
        tenant.phone_number = self.cleaned_data.get('phone_number', '')
        if commit:
            tenant.save()
        return tenant


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['tenant', 'date', 'amount', 'type', 'status']


# Formularze zgłoszeń i konserwacji
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['apartment', 'title', 'description', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class BuildingAlertForm(forms.ModelForm):
    class Meta:
        model = BuildingAlert
        fields = ['apartment', 'title', 'message', 'alert_type', 'severity', 'is_active', 'expires_at']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


# Formularze użytkowników i autoryzacji
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


# Formularze importu danych
class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label="Wybierz plik CSV",
        help_text="Obsługiwane formaty: CSV z separatorem przecinka, średnika lub tabulatora."
    )


class AdvancedCSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label="Wybierz plik CSV",
        help_text="Obsługiwane formaty: CSV z separatorem przecinka, średnika lub tabulatora."
    )
    model_type = forms.ChoiceField(
        label="Typ danych",
        choices=[
            ('apartment', 'Mieszkania'),
            ('utility_consumption', 'Zużycie mediów'),
            ('payment', 'Płatności')
        ],
        help_text="Wybierz typ danych do importu"
    )
    date_format = forms.ChoiceField(
        label="Format daty",
        choices=[
            ('%Y-%m-%d', 'RRRR-MM-DD'),
            ('%d-%m-%Y', 'DD-MM-RRRR'),
            ('%d.%m.%Y', 'DD.MM.RRRR'),
            ('%m/%d/%Y', 'MM/DD/RRRR')
        ],
        help_text="Wybierz format daty używany w pliku CSV",
        initial='%Y-%m-%d'
    )
    has_header = forms.BooleanField(
        label="Plik zawiera nagłówki",
        initial=True,
        required=False,
        help_text="Zaznacz, jeśli pierwszy wiersz pliku zawiera nazwy kolumn"
    )


class UtilityConsumptionImportForm(forms.Form):
    csv_file = forms.FileField(label="Wybierz plik CSV z danymi zużycia")

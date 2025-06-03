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
class TenantForm(forms.ModelForm):
    # Tworzymy nowego użytkownika przy dodawaniu lokatora
    username = forms.CharField(label='Nazwa użytkownika')
    password1 = forms.CharField(label='Hasło', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Powtórz hasło', widget=forms.PasswordInput)
    
    class Meta:
        model = Tenant
        fields = ['apartment', 'num_occupants']
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Hasła nie pasują do siebie")
        
        return cleaned_data
    
    def save(self, commit=True):
        # Tworzenie nowego użytkownika
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1']
        )
        
        # Tworzenie lokatora powiązanego z nowym użytkownikiem
        tenant = super().save(commit=False)
        tenant.user = user
        
        if commit:
            tenant.save()
        
        return tenant

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
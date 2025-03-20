from django import forms
from .models import WasteDisposalRecord
from .models import RedeemHistory

class RedeemForm(forms.ModelForm):
    REWARDS = [
        ('Sick Leave', 'Sick Leave (70 Credits)'),
        ('Library Access', 'Library Access (50 Credits)'),
    ]

    reward = forms.ChoiceField(choices=REWARDS, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = RedeemHistory
        fields = ['reward']

class WasteDisposalForm(forms.ModelForm):
    barcode_image = forms.ImageField(required=False)  # ✅ Allow image upload

    class Meta:
        model = WasteDisposalRecord
        fields = ['waste_type', 'barcode_image']
        widgets = {
            'waste_type': forms.Select(choices=[
                ('Plastic', 'Plastic'),
                ('Paper', 'Paper'),
                ('Glass', 'Glass'),
                ('Metal', 'Metal'),
                ('Organic', 'Organic'),
            ], attrs={'class': 'form-control'})
        }

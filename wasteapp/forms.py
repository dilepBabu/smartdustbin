from django import forms
from .models import WasteDisposalRecord

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

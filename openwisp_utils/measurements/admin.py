from django import forms

from .models import MetricCollectionConsent


class MetricCollectionConsentForm(forms.ModelForm):
    class Meta:
        model = MetricCollectionConsent
        widgets = {'user_consented': forms.CheckboxInput(attrs={'class': 'bold'})}
        fields = ['user_consented']

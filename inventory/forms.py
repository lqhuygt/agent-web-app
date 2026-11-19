from django import forms


class StockAdjustmentForm(forms.Form):
    delta = forms.IntegerField(help_text='Positive to add stock; negative to remove stock.')
    reason = forms.CharField(max_length=255, widget=forms.Textarea(attrs={'rows': 3}))

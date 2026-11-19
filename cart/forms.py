from django import forms


class CartQuantityForm(forms.Form):
    variant_id = forms.IntegerField(min_value=1)
    quantity = forms.IntegerField(min_value=0)

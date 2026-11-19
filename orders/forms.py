from django import forms


class CheckoutForm(forms.Form):
    idempotency_key = forms.UUIDField(widget=forms.HiddenInput)
    name = forms.CharField(label='Họ và tên', min_length=2, max_length=120)
    phone = forms.CharField(label='Số điện thoại', min_length=9, max_length=16)
    address = forms.CharField(label='Địa chỉ nhận hàng', min_length=8, max_length=300, widget=forms.Textarea(attrs={'rows': 3}))
    note = forms.CharField(label='Ghi chú', required=False, max_length=500, widget=forms.Textarea(attrs={'rows': 3}))

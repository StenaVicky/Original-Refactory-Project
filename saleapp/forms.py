from django import forms
from django.utils.text import slugify
from .models import Category, Product


class PlainFormMixin:
    use_required_attribute = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            for attr in ("max_length", "min_length", "min_value", "max_value"):
                if hasattr(field, attr):
                    setattr(field, attr, None)
            for attr in ("maxlength", "minlength", "min", "max", "step", "required"):
                field.widget.attrs.pop(attr, None)


class CategoryForm(PlainFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["category_name", "slug"]

    def clean_category_name(self):
        name = self.cleaned_data["category_name"].strip()
        if len(name) < 3:
            raise forms.ValidationError("Category name must be at least three characters")
        return name

    def clean_slug(self):
        slug = slugify(self.cleaned_data["slug"])
        if not slug:
            raise forms.ValidationError("Enter a valid slug")
        return slug


class ProductForm(PlainFormMixin, forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all())
    product_name = forms.CharField(max_length=100)
    description = forms.CharField(widget=forms.Textarea)

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance

    def clean_product_name(self):
        name = self.cleaned_data["product_name"].strip()
        if len(name) < 3:
            raise forms.ValidationError("Product name must be at least three characters")
        return name

    def clean_description(self):
        description = self.cleaned_data["description"].strip()
        if len(description) < 3:
            raise forms.ValidationError("Description must be at least three characters")
        return description

    def save(self):
        product = self.instance or Product()
        product.category_name = self.cleaned_data["category"]
        product.product_name = self.cleaned_data["product_name"]
        product.description = self.cleaned_data["description"]
        product.save()
        return product


class SaleForm(PlainFormMixin, forms.Form):
    customer_name = forms.CharField(max_length=255, required=False)
    distance = forms.DecimalField(
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        widget=forms.TextInput,
        error_messages={
            "invalid": "Enter a valid distance",
            "min_value": "Distance must be greater than zero",
            "required": "Distance is required",
        },
    )

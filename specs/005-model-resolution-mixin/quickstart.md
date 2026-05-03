# Quickstart: Model Resolution Mixin

**Branch**: `005-model-resolution-mixin` | **Date**: 2026-05-03

`ModelInfoMixin` is the foundation of all model-driven views in django-mvp. It resolves the model class for a view and makes human-readable model metadata available in the template context automatically — no extra configuration required beyond what you'd normally write for a Django class-based view.

---

## What you get

Any view that inherits from `ModelInfoMixin` (directly or via `PageObjectMixin`, `MVPDetailView`, `MVPCreateView`, etc.) automatically provides:

```html
{{ model_info.verbose_name }}         {# e.g. "product" #}
{{ model_info.verbose_name_plural }}  {# e.g. "products" #}
{{ model_info.app_label }}            {# e.g. "catalogue" #}
{{ model_info.model_name }}           {# e.g. "product" #}
```

---

## Configuration styles

You do not need to do anything special. Use whichever Django style you would normally use for your view — `ModelInfoMixin` resolves the model automatically.

### Style 1: Direct model attribute (most common)

```python
from mvp.views import MVPDetailView

class ProductDetailView(MVPDetailView):
    model = Product
```

### Style 2: Custom queryset

```python
class ActiveProductListView(MVPListView):
    queryset = Product.objects.filter(is_active=True)
```

### Style 3: ModelForm class

```python
class ProductCreateView(MVPCreateView):
    form_class = ProductForm  # ProductForm is a ModelForm for Product
```

### Style 4: Pre-fetched object (runtime binding)

This is handled automatically when Django resolves `self.object` via `get_object()`. You do not need to set `model_info` yourself.

---

## Custom resolution (advanced)

If your view selects a model dynamically — for example, based on a URL parameter or a tenant configuration — override `get_model_class()`:

```python
class TenantAwareDetailView(MVPDetailView):
    def get_model_class(self):
        tenant = self.request.tenant
        return tenant.get_content_model()  # returns a Django model class
```

All downstream features (page title, breadcrumbs, CRUD directory) will reflect the dynamically selected model automatically.

---

## Reading model metadata in Python

If you need the resolved model class in view Python code (not in templates), call `get_model_class()` directly:

```python
class ProductDetailView(MVPDetailView):
    model = Product

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        model_cls = self.get_model_class()  # → Product
        ctx["field_count"] = len(model_cls._meta.get_fields())
        return ctx
```

---

## Troubleshooting

**`ImproperlyConfigured: MyView inherits from \`ModelInfoMixin\` but could not determine a model class.`**

Your view does not provide any of the four supported model configuration styles. Set one of:

- `model = MyModel` on the view class
- `queryset = MyModel.objects.all()` on the view class
- `form_class = MyModelForm` where `MyModelForm` is a `ModelForm` for `MyModel`
- or override `get_model_class()` to return your model class directly

---

## Import

```python
# Canonical
from mvp.views.base import ModelInfoMixin

# Via top-level package (also supported)
from mvp.views import ModelInfoMixin
```

In practice you will rarely import `ModelInfoMixin` directly — it is already included in `MVPDetailView`, `MVPCreateView`, `MVPUpdateView`, `MVPDeleteView`, and `MVPListView` through `PageObjectMixin`.

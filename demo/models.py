"""Example models for demonstrating list and detail views."""

from django.db import models
from django.urls import reverse


class Category(models.Model):
    """Category model for organizing products."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50, blank=True, help_text="Icon name (e.g., 'folder', 'tag')"
    )
    color = models.CharField(
        max_length=20, default="primary", help_text="Bootstrap color variant"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options."""

        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        """String representation."""
        return self.name

    def get_absolute_url(self):
        """Get absolute URL."""
        return reverse("category_detail", kwargs={"slug": self.slug})


class Product(models.Model):
    """Product model for demonstrating various list and detail views."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    # Basic fields
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)

    # Numeric fields
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    # Status fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="medium"
    )
    is_featured = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)

    # Date fields
    release_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Metadata
    tags = models.CharField(
        max_length=200, blank=True, help_text="Comma-separated tags"
    )
    sku = models.CharField(max_length=50, unique=True, blank=True)
    barcode = models.CharField(max_length=100, blank=True)

    class Meta:
        """Meta options."""

        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "is_available"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        """String representation."""
        return self.name

    def get_absolute_url(self):
        """Get absolute URL."""
        return reverse("product_detail", kwargs={"slug": self.slug})

    @property
    def tag_list(self):
        """Return tags as a list."""
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]

    @property
    def stock_status(self):
        """Return stock status indicator."""
        if self.stock == 0:
            return "out_of_stock"
        elif self.stock < 10:
            return "low_stock"
        return "in_stock"


class Article(models.Model):
    """Article model for blog/content demonstrations."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("review", "Under Review"),
        ("published", "Published"),
    ]

    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True)
    author = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="articles"
    )
    excerpt = models.TextField(max_length=500)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    views = models.IntegerField(default=0)
    read_time = models.IntegerField(
        default=5, help_text="Estimated read time in minutes"
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.CharField(max_length=200, blank=True)

    class Meta:
        """Meta options."""

        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        """String representation."""
        return self.title

    def get_absolute_url(self):
        """Get absolute URL."""
        return reverse("article_detail", kwargs={"slug": self.slug})


class Task(models.Model):
    """Task model for project management demonstrations."""

    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("in_progress", "In Progress"),
        ("review", "In Review"),
        ("done", "Done"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="medium"
    )
    assignee = models.CharField(max_length=100, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks"
    )
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_hours = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    actual_hours = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    class Meta:
        """Meta options."""

        ordering = ["-priority", "due_date", "-created_at"]

    def __str__(self):
        """String representation."""
        return self.title

    def get_absolute_url(self):
        """Get absolute URL."""
        return reverse("task_detail", kwargs={"pk": self.pk})

    @property
    def is_overdue(self):
        """Check if task is overdue."""
        from django.utils import timezone

        if self.due_date and self.status != "done":
            return self.due_date < timezone.now().date()
        return False

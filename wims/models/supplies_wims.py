from django.db import models

class Supplier(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing ID
    name_company = models.CharField(max_length=150, unique=True)  # Supplier company name
    description = models.TextField(blank=True, null=True)  # Optional description
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for record creation
    updated_at = models.DateTimeField(auto_now=True)  # Auto-update timestamp

    class Meta:
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"
        ordering = ["name_company"]  # Order alphabetically

    def __str__(self):
        return self.name_company  # Show company name when printed

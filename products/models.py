from django.db import models

class Category(models.Model):
    """Model for product categories"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Product(models.Model):
    """Model for SafetyPlus products that can be recommended"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    link = models.URLField()
    
    def __str__(self):
        return self.name
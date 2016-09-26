from django.db import models

class Categories(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    class Meta:
        db_table = 'categories'
        app_label = 'target_models'

class Suppliers(models.Model):
    id = models.IntegerField(primary_key=True)
    address_street = models.TextField()
    address_city = models.TextField()
    address_state = models.TextField()
    address_zipcode = models.TextField()
    address_country = models.TextField()
    concurrency = models.IntegerField(null=False)

    class Meta:
        db_table = 'suppliers'
        app_label = 'target_models'

class Products(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    description = models.TextField()
    release_date = models.DateTimeField()
    discontinued_date = models.DateTimeField()
    rating = models.IntegerField()
    price = models.DecimalField(10, 0)

    products_category_categories_id = models.IntegerField()
    products_supplier_suppliers_id = models.IntegerField()

    class Meta:
        db_table = 'products'
        app_label = 'target_models'

from factory.django import DjangoModelFactory



class CompanyFactory(DjangoModelFactory):
    """Company factory."""
    
    class Meta:
        model = 
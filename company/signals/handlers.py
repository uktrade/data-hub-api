from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from company.models import Advisor, Team, Company, CompaniesHouseCompany, Contact, Interaction
from core.utils import model_to_dictionary
from es.connector import ESConnector


# Create a Django user when an advisor is created
@receiver(post_save, sender=Advisor)
def create_user_for_advisor(instance, created, **kwargs):
    if created and not instance.user:
        user_model = get_user_model()
        user = user_model.objects.create(
            email=instance.email,
            first_name=instance.first_name,
            last_name=instance.last_name,
            username=instance.email.split('@')[0],
        )
        user.set_unusable_password()
        instance(user=user)
        instance.save()


# Create an advisor when a user is created (ie using the shell)
# Users should be created through advisors, this covers the case of automated tests and users created with
# the management command
@receiver(post_save, sender=User)  # cannot use get_user_model() because app registry is not initialised
def create_advisor_for_user(instance, created, **kwargs):
    if created:
        advisor = Advisor(
            user=instance,
            first_name=instance.first_name,
            last_name=instance.last_name,
            dit_team=Team.objects.get(name='UKTI HQ (DR)'),
            email=instance.email if instance.email else None
        )
        advisor.save(as_korben=True)  # don't talk to Korben, this is not an Advisor we want to save in CDMS!


# Write to ES stuff
@receiver((post_save, m2m_changed))
def save_to_es(sender, instance, **kwargs):
    """Save to ES."""

    if sender in (Company, CompaniesHouseCompany, Contact, Interaction):
        es_connector = ESConnector()
        doc_type = type(instance)._meta.db_table  # cannot access _meta from the instance
        data = model_to_dictionary(instance)
        es_connector.save(doc_type=doc_type, data=data)

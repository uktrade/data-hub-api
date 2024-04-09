import os
import random
import time

from collections import defaultdict
from datetime import timedelta

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db.models.signals import (
    m2m_changed,
    post_delete,
    post_init,
    post_migrate,
    post_save,
    pre_delete,
    pre_init,
    pre_migrate,
    pre_save,
)

from datahub.company.models.adviser import Advisor
from datahub.company.models.company import Company
from datahub.company.test.factories import (
    AdviserFactory,
    ArchivedCompanyFactory,
    # ArchivedCompanyFactory,
    CompanyFactory,
    CompanyWithAreaFactory,
    DuplicateCompanyFactory,
    # CompanyWithAreaFactory,
    ContactFactory,
    ContactWithOwnAddressFactory,
    ContactWithOwnAreaFactory,
    SubsidiaryFactory,
)
from datahub.metadata.models import Team


class DisableSignals:
    def __init__(self, disabled_signals=None):
        self.stashed_signals = defaultdict(list)
        self.disabled_signals = disabled_signals or [
            pre_init,
            post_init,
            pre_save,
            post_save,
            pre_delete,
            post_delete,
            pre_migrate,
            post_migrate,
            m2m_changed,
        ]

    def __enter__(self):
        for signal in self.disabled_signals:
            self.disconnect(signal)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for signal in list(self.stashed_signals):
            self.reconnect(signal)

    def disconnect(self, signal):
        self.stashed_signals[signal] = signal.receivers
        signal.receivers = []

    def reconnect(self, signal):
        signal.receivers = self.stashed_signals.get(signal, [])
        del self.stashed_signals[signal]


# Disable open search indexing
with DisableSignals():
    start_time = time.time()

    # Pre fetch Metadata
    teams = list(Team.objects.all())

    advisers = Advisor.objects.all()

    # In February 2024 there were 18,000 advisers, 500,000 companies, and 950,000 contacts.
    # Alter number of adivsers below to create larger or smaller data set.
    # Generate Advisers
    print('Generating advisers')  # noqa
    for index in range(10):
        AdviserFactory(dit_team=random.choice(teams))
        if index % 10 == 0:
            print('.', end='')  # noqa
    advisers = Advisor.objects.all()

    print(f'Generated {advisers.count} advisers')  # noqa

    # # Generate base companies
    print('\nGenerating Companies')  # noqa
    for index, adviser in enumerate(advisers):
        CompanyFactory.create_batch(
            random.randint(0, 25),
            created_by=adviser,
            modified_by=random.choice(advisers),
        )
        if index % 10 == 0:
            print('.', end='')  # noqa

    print('\nGenerating Company variations')  # noqa
    companies = Company.objects.all()
    # The ratios of the below types of companies do not reflect the live database.
    # Generate different type of companies
    for index, adviser in enumerate(advisers):
        SubsidiaryFactory.create_batch(
            random.randint(0, 25),
            created_by=adviser,
            modified_by=random.choice(advisers),
            global_headquarters=random.choice(companies),
        )
        CompanyWithAreaFactory.create_batch(
            random.randint(0, 1),
            created_by=adviser,
            modified_by=random.choice(advisers),
        )
        ArchivedCompanyFactory.create_batch(
            random.randint(0, 1),
            created_by=adviser,
            modified_by=adviser,
        )
        DuplicateCompanyFactory.create_batch(
            random.randint(0, 1),
            created_by=adviser,
            modified_by=adviser,
            transferred_by=random.choice(advisers),
            transferred_to=random.choice(companies),
        )


        def generateContacts(advisers, min, max):
            print('\nGenerating contacts on advisers')
            for index, adviser in enumerate(advisers):
                ContactFactory.create_batch(
                    random.randint(min, max),
                    created_by=random.choice(advisers),
                    modified_by=random.choice(advisers),
                )

            print('\nGenerating contacts on advisers with a different address from company')
            for index, adviser in enumerate(advisers):
                ContactWithOwnAddressFactory.create_batch(
                    random.randint(min, max),
                    created_by=random.choice(advisers),
                    modified_by=random.choice(advisers),
                )

            print(
                '\nGenerating contacts on advisers with a different address from the contact company that includes an '
                'area')
            for index, adviser in enumerate(advisers):
                ContactWithOwnAreaFactory.create_batch(
                    random.randint(min, max),
                    created_by=random.choice(advisers),
                    modified_by=random.choice(advisers),
                )


        print('\nGenerating Company variations')  # noqa
        companies = Company.objects.all()
        # The ratios of the below types of companies do not reflect the live database.
        # Generate different type of companies
        for index, adviser in enumerate(advisers):
            SubsidiaryFactory.create_batch(
                random.randint(0, 25),
                created_by=adviser,
                modified_by=random.choice(advisers),
                global_headquarters=random.choice(companies),
            )
            CompanyWithAreaFactory.create_batch(
                random.randint(0, 1),
                created_by=adviser,
                modified_by=random.choice(advisers),
            )

        # Show a sign of life every now and then
        if index % 10 == 0:
            print('.', end='')  # noqa

        # The below ratio of contacts to companies does not reflect the live database.
        # for company in companies:
        #     ContactFactory.create_batch(
        #         random.randint(1, 2),
        #         company=company,
        #         created_by=adviser,
        # )

    elapsed = time.time() - start_time
    print(f'{timedelta(seconds=elapsed)}')  # noqa

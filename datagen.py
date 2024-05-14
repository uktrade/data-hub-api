import os
import time

from datetime import timedelta
from pprint import pprint

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from datagen.constants import MODEL_INFO
from datagen.generators.adviser import generate_advisers
from datagen.generators.company import generate_companies
from datagen.generators.investment_project import generate_investment_projects
from datagen.utils import DisableSignals

from datahub.company.models.adviser import Advisor
from datahub.company.models.company import Company


def get_model_counts():
    """Returns a dictionary containing counts of each model."""
    return {
        model_name: MODEL_INFO[model_name]['model'].objects.count()
        for model_name in MODEL_INFO.keys()
    }


# Disable open search indexing
with DisableSignals():

    # Preamble
    print('\nGenerator started')  # noqa
    start_time = time.time()
    print('\nStarting counts of models:')  # noqa
    starting_model_counts = get_model_counts()
    pprint(starting_model_counts)  # noqa

    # Specify quantities
    NUMBER_OF_ADVISERS = 50
    NUMBER_OF_COMPANIES = 200
    NUMBER_OF_INVESTMENT_PROJECTS = 300

    # Generate Advisers
    generate_advisers(NUMBER_OF_ADVISERS)
    advisers = Advisor.objects.all()

    # Generate Companies
    generate_companies(NUMBER_OF_COMPANIES, advisers)
    companies = Company.objects.all()

    # Generate Investment Projects
    generate_investment_projects(
        NUMBER_OF_INVESTMENT_PROJECTS,
        advisers,
        companies,
    )

    # End matter
    print('\nFinal counts of models:')  # noqa
    final_model_counts = get_model_counts()
    pprint(final_model_counts)  # noqa
    print('\nDifference in counts of models:')  # noqa
    pprint(  # noqa
        {
            key: final_model_counts[key] - starting_model_counts[key]
            for key in starting_model_counts.keys()
        },
    )
    elapsed_time = time.time() - start_time
    print(f'\nTotal run time: {timedelta(seconds=elapsed_time)} (H:MM:SS.SSSSSS)\n')  # noqa

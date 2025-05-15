from datahub.documents.utils import get_s3_client_for_bucket
from contextlib import closing
import codecs
import csv


def process_row(company_name, companies):
    """Process a single row."""
    company_name = company_name.lower()
    if company_name in companies:
        return True
    if 'ltd' in company_name:
        company_name = company_name.replace('ltd', 'limited')
    elif 'limited' in company_name:
        company_name = company_name.replace('limited', 'ltd')
    else:
        return False
    if company_name in companies:
        return True
    return False


# Bucket setup.
s3_client = get_s3_client_for_bucket('default')
bucket = 'upload.datahub.dev.uktrade.io'
filename_key = 'ka.csv'
response = s3_client.get_object(
    Bucket=bucket,
    Key=filename_key,
)['Body']
# Use set as much faster with all lower case company names.
companies = Company.objects.all().values_list('name', flat=True)
companies_set = set(x.lower() for x in companies)
with closing(response):
    csvfile = codecs.getreader('utf-8')(response)
    reader = csv.DictReader(csvfile)
    # For logging.
    companies_found = {}
    companies_found_count = 0
    companies_not_found = {}
    companies_not_found_count = 0
    total_rows = 0
    for row in reader:
        award_year = row['Year of Award']
        # Skip 2025 and 2024
        if award_year in {'2025', '2024'}:
            continue
        # Create dictionary of years and matches for logging.
        if award_year not in companies_found:
            companies_found[award_year] = []
        if award_year not in companies_not_found:
            companies_not_found[award_year] = []
        total_rows += 1
        company_name = row['Company Name']
        successful = process_row(company_name, companies_set)
        if successful:
            companies_found_count += 1
            companies_found[award_year].append(company_name)
        else:
            companies_not_found_count += 1
            companies_not_found[award_year].append(company_name)
    print(companies_found)
    print(companies_not_found)
    print(f"Processed {total_rows}. {companies_found_count} out of {companies_not_found_count} were matched.")
    for year, _ in companies_found.items():
        print(f"For year: {year}.")
        print(f"There were: {len(companies_found[year])} matched and {len(companies_not_found[year])} unmatched.")
        print("--------------------------")
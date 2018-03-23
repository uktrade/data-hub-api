from datahub.company.constants import BusinessTypeConstant

# This mapping determines which Companies House company categories we are interested in,
# and what their corresponding business type should be in Data Hub.
#
# Any company categories that are mapped to a falsey value are not loaded to the database by the
# sync_ch command.
#
# Additionally, the Companies House company view returns a business type using this mapping. That
# business type is then used by the front end when POSTing to /v3/company.
COMPANY_CATEGORY_TO_BUSINESS_TYPE_MAPPING = {
    # Address not available/main registration not with Companies House
    'charitable incorporated organisation': None,
    'community interest company': BusinessTypeConstant.community_interest_company,
    'european public limited-liability company (se)': BusinessTypeConstant.public_limited_company,
    # Address not available/main registration with FCA
    'industrial and provident society': None,
    # Address not available/main registration with FCA
    'investment company with variable capital': None,
    # Address not available/main registration with FCA
    'investment company with variable capital (securities)': None,
    # Address not available/main registration with FCA
    'investment company with variable capital(umbrella)': None,
    'limited liability partnership': BusinessTypeConstant.limited_liability_partnership,
    'limited partnership': BusinessTypeConstant.limited_partnership,
    # Historical
    'old public company': BusinessTypeConstant.company,
    # Foreign and other irrelevant companies
    'other company type': None,
    "pri/lbg/nsc (private, limited by guarantee, no share capital, use of 'limited' exemption)":
        BusinessTypeConstant.private_limited_company,
    'pri/ltd by guar/nsc (private, limited by guarantee, no share capital)':
        BusinessTypeConstant.private_limited_company,
    # Section 30 is the limited exemption
    'priv ltd sect. 30 (private limited company, section 30 of the companies act)':
        BusinessTypeConstant.private_limited_company,
    'private limited company': BusinessTypeConstant.private_limited_company,
    'private unlimited': BusinessTypeConstant.company,
    'private unlimited company': BusinessTypeConstant.company,
    # Address not available/main registration with FCA
    'protected cell company': None,
    'public limited company': BusinessTypeConstant.public_limited_company,
    # Address not available/main registration with FCA
    'registered society': None,
    # Address not available
    'royal charter company': None,
    # Address not available/main registration not with Companies House
    'scottish charitable incorporated organisation': None,
    # Scottish qualifying partnership, generally have a foreign address
    'scottish partnership': None,
}

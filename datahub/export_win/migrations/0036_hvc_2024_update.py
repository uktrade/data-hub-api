
from django.db import migrations

import csv
from io import StringIO

from django.db.transaction import atomic

from datahub.export_win.models import HVC


# Note: We are copying the 2023/24 HVCs forward as 2024/25.

hvcs_tsv = """code	name
 E002	Asia-Pacific ANZ Defence & Security: E002
 E005	Asia-Pacific ANZ Technology: E005
 E006	Asia-Pacific ANZ Financial & Professional Services: E006
 E007	Azerbaijan Oil & Gas: E007
 E008	Bahrain Defence & Security: E008
 E011	Belgium Defence & Security: E011
 E012	Brazil Marine: E012
 E014	Brazil Oil & Gas: E014
 E015	Canada Defence & Security: E015
 E017	Europe Central Automotive: E017
 E018	Europe Central Defence & Security: E018
 E019	Europe Central Financial & Professional Services: E019
 E020	Europe Central Nuclear: E020
 E022	China Marine: E022
 E023	China Aerospace: E023
 E024	China Automotive: E024
 E025	China Consumer & Retail: E025
 E026	China Creative: E026
 E027	China Technology: E027
 E028	China & Hong Kong Education: E028
 E029	China Nuclear: E029
 E031	China & Hong Kong Financial & Professional Services: E031
 E032	China Food & Drink: E032
 E033	China & Hong Kong Healthcare: E033
 E038	China & Hong Kong Life Sciences: E038
 E042	Africa Oil & Gas: E042
 E043	Africa Renewables: E043
 E045	France Aerospace: E045
 E046	France Defence & Security: E046
 E047	France Nuclear: E047
 E049	Germany Automotive: E049
 E050	Europe West Chemicals: E050
 E051	Germany Consumer & Retail: E051
 E052	Germany Defence & Security: E052
 E053	Europe West Nuclear: E053
 E054	Europe West Food & Drink: E054
 E058	Hong Kong Creative: E058
 E064	India Agritech: E064
 E065	India Chemicals: E065
 E067	India Creative: E067
 E068	India Defence & Security: E068
 E069	India Technology: E069
 E070	India Oil & Gas: E070
 E072	India Financial & Professional Services: E072
 E073	India Food & Drink: E073
 E074	India Healthcare Life Sciences: E074
 E079	Indonesia Defence & Security: E079
 E081	Iraq Oil & Gas: E081
 E083	Italy Consumer & Retail: E083
 E085	Japan Defence & Security: E085
 E086	Japan Technology: E086
 E087	Japan Nuclear: E087
 E089	Asia-Pacific North East Asia Life Sciences: E089
 E091	Kazakhstan Oil & Gas: E091
 E092	Kuwait Defence & Security: E092
 E094	LATAC Education: E094
 E095	LATAC Financial & Professional Services: E095
 E096	LATAC Food & Drink: E096
 E099	Mexico Oil & Gas: E099
 E103	Malaysia Defence & Security: E103
 E104	Malaysia Technology: E104
 E105	Europe South Defence & Security: E105
 E106	Europe South Life Sciences: E106
 E107	LATAC AESC Automotive: E107
 E111	Middle East Education: E111
 E112	Middle East Nuclear: E112
 E117	Nigeria Oil & Gas: E117
 E118	North America Food & Drink: E118
 E119	Europe West Renewables: E119
 E122	Oman Defence & Security: E122
 E123	Oman Oil & Gas: E123
 E125	Phillipines Technology: E125
 E129	Qatar Defence & Security: E129
 E132	Saudi Arabia Consumer & Retail: E132
 E133	Saudi Arabia Defence & Security: E133
 E135	Saudi Arabia Oil & Gas: E135
 E140	Singapore Defence & Security: E140
 E141	Singapore Technology: E141
 E145	Africa Defence & Security: E145
 E146	Asia-Pacific South East Asia Education: E146
 E148	South Korea Marine: E148
 E149	South Korea Consumer & Retail: E149
 E150	South Korea Defence & Security: E150
 E151	South Korea and Taiwan Technology: E151
 E153	Africa Agritech: E153
 E155	Spain Chemicals: E155
 E156	Spain Consumer & Retail: E156
 E158	Sweden Consumer & Retail: E158
 E159	Europe North Defence & Security: E159
 E163	Thailand Defence & Security: E163
 E165	Turkey Defence & Security: E165
 E171	Ukraine Agritech: E171
 E174	Middle East Creative: E174
 E175	UAE Defence & Security: E175
 E182	USA Aerospace: E182
 E184	USA Automotive: E184
 E186	USA Consumer & Retail: E186
 E187	North America Creative: E187
 E188	USA Defence & Security: E188
 E189	USA Technology: E189
 E191	North America Financial & Professional Services: E191
 E194	USA Life Sciences: E194
 E209	Africa North Defence & Security: E209
 E212	Taiwan Renewables: E212
 E218	Austria Defence & Security: E218
 E219	Europe Central Consumer & Retail: E219
 E220	Europe Central Healthcare: E220
 E223	LATAC Defence & Security: E223
 E224	Global Aerospace: E224
 E225	Global Sports Economy: E225
 E226	Global Sports Economy: E226
 E227	India AESC Automotive: E227
 E228	Indonesia Renewables: E228
 E229	Iran Consumer & Retail: E229
 E230	LATAC Life Sciences: E230
 E232	Middle East Healthcare: E232
 E233	Europe North Food & Drink: E233
 E236	Asia-Pacific South East Asia Financial & Professional Services: E236
 E237	Europe West Agritech: E237
 E238	Switzerland Defence & Security: E238
 E239	Europe West Financial & Professional Services: E239
 E242	Africa Oil & Gas: E242
 E243	Phillipines Defence & Security: E243
 E244	Defence & Security: E244
 E245	USA Space: E245
 E247	LATAC Renewables: E247
 E248	Defence & Security: E248
 E250	India Space: E250
 E251	Asia-Pacific South East Asia Marine: E251
 E255	Thailand Agritech: E255
 E256	Middle East Life Sciences: E256
 E257	Middle East Technology: E257
 E258	Asia-Pacific South East Asia Healthcare: E258
 E263	UAE Food & Drink: E263
 E269	China AESC: E269
 E270	Europe Med Financial & Professional Services: E270
 E271	Europe Technology: E271
 E272	Africa Infrastructure: E272
 E273	ANZ Infrastructure: E273
 E274	APAC Infrastructure: E274
 E275	South Asia Infrastructure: E275
 E276	EECA Infrastructure: E276
 E277	Europe Infrastructure: E277
 E278	MEAP Infrastructure: E278
 E279	North America Infrastructure: E279
 E280	LatAC Infrastructure: E280
 E281	China Infrastructure: E281
"""


def get_rows(text):
    reader = csv.DictReader(StringIO(text), delimiter='\t', skipinitialspace=True)
    return list(reader)


@atomic
def load_hvcs(apps, _):
    hvcs = get_rows(hvcs_tsv)
    for hvc in hvcs:
        hvc = HVC(campaign_id=hvc['code'], name=hvc['name'], financial_year=24)
        hvc.save()


class Migration(migrations.Migration):

    dependencies = [
        ('export_win', '0035_experiencecategories_export_experience'),
    ]

    operations = [
        migrations.RunPython(load_hvcs, migrations.RunPython.noop),
    ]

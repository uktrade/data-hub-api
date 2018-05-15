from collections import namedtuple
from enum import Enum

Constant = namedtuple('Constant', ('name', 'id'))
OrderedConstant = namedtuple('OrderedConstant', ('name', 'id', 'order'))


class Country(Enum):
    """Countries."""

    afghanistan = Constant('Afghanistan', '87756b9a-5d95-e211-a939-e4115bead28a')
    aland_islands = Constant('Aland Islands', '88756b9a-5d95-e211-a939-e4115bead28a')
    albania = Constant('Albania', '945f66a0-5d95-e211-a939-e4115bead28a')
    algeria = Constant('Algeria', '955f66a0-5d95-e211-a939-e4115bead28a')
    american_samoa = Constant('American Samoa', '965f66a0-5d95-e211-a939-e4115bead28a')
    andorra = Constant('Andorra', '975f66a0-5d95-e211-a939-e4115bead28a')
    angola = Constant('Angola', '985f66a0-5d95-e211-a939-e4115bead28a')
    anguilla = Constant('Anguilla', '995f66a0-5d95-e211-a939-e4115bead28a')
    antarctica = Constant('Antarctica', '9a5f66a0-5d95-e211-a939-e4115bead28a')
    antigua_and_barbuda = Constant('Antigua and Barbuda', '9b5f66a0-5d95-e211-a939-e4115bead28a')
    argentina = Constant('Argentina', '9c5f66a0-5d95-e211-a939-e4115bead28a')
    armenia = Constant('Armenia', '9d5f66a0-5d95-e211-a939-e4115bead28a')
    aruba = Constant('Aruba', '9e5f66a0-5d95-e211-a939-e4115bead28a')
    australia = Constant('Australia', '9f5f66a0-5d95-e211-a939-e4115bead28a')
    austria = Constant('Austria', 'a05f66a0-5d95-e211-a939-e4115bead28a')
    azerbaijan = Constant('Azerbaijan', 'a15f66a0-5d95-e211-a939-e4115bead28a')
    bahamas = Constant('Bahamas', 'a25f66a0-5d95-e211-a939-e4115bead28a')
    bahrain = Constant('Bahrain', 'a35f66a0-5d95-e211-a939-e4115bead28a')
    bangladesh = Constant('Bangladesh', 'a45f66a0-5d95-e211-a939-e4115bead28a')
    barbados = Constant('Barbados', 'a55f66a0-5d95-e211-a939-e4115bead28a')
    belarus = Constant('Belarus', 'a65f66a0-5d95-e211-a939-e4115bead28a')
    belgium = Constant('Belgium', 'a75f66a0-5d95-e211-a939-e4115bead28a')
    belize = Constant('Belize', 'a85f66a0-5d95-e211-a939-e4115bead28a')
    benin = Constant('Benin', 'a95f66a0-5d95-e211-a939-e4115bead28a')
    bermuda = Constant('Bermuda', 'aa5f66a0-5d95-e211-a939-e4115bead28a')
    bhutan = Constant('Bhutan', 'ab5f66a0-5d95-e211-a939-e4115bead28a')
    bolivia = Constant('Bolivia', 'ac5f66a0-5d95-e211-a939-e4115bead28a')
    bosnia_and_herzegovina = Constant(
        'Bosnia and Herzegovina', 'ad5f66a0-5d95-e211-a939-e4115bead28a'
    )
    botswana = Constant('Botswana', 'ae5f66a0-5d95-e211-a939-e4115bead28a')
    bouvet_island = Constant('Bouvet Island', 'af5f66a0-5d95-e211-a939-e4115bead28a')
    brazil = Constant('Brazil', 'b05f66a0-5d95-e211-a939-e4115bead28a')
    british_indian_ocean_territory = Constant(
        'British Indian Ocean Territory', 'b15f66a0-5d95-e211-a939-e4115bead28a'
    )
    british_virgin_islands = Constant(
        'British Virgin Islands', 'b25f66a0-5d95-e211-a939-e4115bead28a'
    )
    brunei = Constant('Brunei', '56af72a6-5d95-e211-a939-e4115bead28a')
    bulgaria = Constant('Bulgaria', '57af72a6-5d95-e211-a939-e4115bead28a')
    burkina = Constant('Burkina', '58af72a6-5d95-e211-a939-e4115bead28a')
    burma = Constant('Burma', '59af72a6-5d95-e211-a939-e4115bead28a')
    burundi = Constant('Burundi', '5aaf72a6-5d95-e211-a939-e4115bead28a')
    cambodia = Constant('Cambodia', '5baf72a6-5d95-e211-a939-e4115bead28a')
    cameroon = Constant('Cameroon', '5caf72a6-5d95-e211-a939-e4115bead28a')
    canada = Constant('Canada', '5daf72a6-5d95-e211-a939-e4115bead28a')
    cape_verde = Constant('Cape Verde', '5eaf72a6-5d95-e211-a939-e4115bead28a')
    cayman_islands = Constant('Cayman Islands', '5faf72a6-5d95-e211-a939-e4115bead28a')
    central_african_republic = Constant(
        'Central African Republic', '60af72a6-5d95-e211-a939-e4115bead28a'
    )
    chad = Constant('Chad', '61af72a6-5d95-e211-a939-e4115bead28a')
    chile = Constant('Chile', '62af72a6-5d95-e211-a939-e4115bead28a')
    china = Constant('China', '63af72a6-5d95-e211-a939-e4115bead28a')
    christmas_island = Constant('Christmas Island', '64af72a6-5d95-e211-a939-e4115bead28a')
    cocos_keeling_islands = Constant(
        'Cocos (Keeling) Islands', '65af72a6-5d95-e211-a939-e4115bead28a'
    )
    colombia = Constant('Colombia', '66af72a6-5d95-e211-a939-e4115bead28a')
    comoros = Constant('Comoros', '67af72a6-5d95-e211-a939-e4115bead28a')
    congo = Constant('Congo', '69af72a6-5d95-e211-a939-e4115bead28a')
    congo_democratic_republic = Constant(
        'Congo (Democratic Republic)', '68af72a6-5d95-e211-a939-e4115bead28a'
    )
    cook_islands = Constant('Cook Islands', '6aaf72a6-5d95-e211-a939-e4115bead28a')
    costa_rica = Constant('Costa Rica', '6baf72a6-5d95-e211-a939-e4115bead28a')
    croatia = Constant('Croatia', '6caf72a6-5d95-e211-a939-e4115bead28a')
    cuba = Constant('Cuba', '6daf72a6-5d95-e211-a939-e4115bead28a')
    cyprus = Constant('Cyprus', '6eaf72a6-5d95-e211-a939-e4115bead28a')
    czech_republic = Constant('Czech Republic', '6faf72a6-5d95-e211-a939-e4115bead28a')
    denmark = Constant('Denmark', '70af72a6-5d95-e211-a939-e4115bead28a')
    djibouti = Constant('Djibouti', '71af72a6-5d95-e211-a939-e4115bead28a')
    dominica = Constant('Dominica', '72af72a6-5d95-e211-a939-e4115bead28a')
    dominican_republic = Constant('Dominican Republic', '73af72a6-5d95-e211-a939-e4115bead28a')
    east_timor = Constant('East Timor', '74af72a6-5d95-e211-a939-e4115bead28a')
    ecuador = Constant('Ecuador', '75af72a6-5d95-e211-a939-e4115bead28a')
    egypt = Constant('Egypt', '76af72a6-5d95-e211-a939-e4115bead28a')
    el_salvador = Constant('El Salvador', 'd2f682ac-5d95-e211-a939-e4115bead28a')
    equatorial_guinea = Constant('Equatorial Guinea', 'd3f682ac-5d95-e211-a939-e4115bead28a')
    eritrea = Constant('Eritrea', 'd4f682ac-5d95-e211-a939-e4115bead28a')
    estonia = Constant('Estonia', 'd5f682ac-5d95-e211-a939-e4115bead28a')
    ethiopia = Constant('Ethiopia', 'd6f682ac-5d95-e211-a939-e4115bead28a')
    falkland_islands = Constant('Falkland Islands', 'd7f682ac-5d95-e211-a939-e4115bead28a')
    faroe_islands = Constant('Faroe Islands', 'd8f682ac-5d95-e211-a939-e4115bead28a')
    fiji = Constant('Fiji', 'd9f682ac-5d95-e211-a939-e4115bead28a')
    finland = Constant('Finland', 'daf682ac-5d95-e211-a939-e4115bead28a')
    france = Constant('France', '82756b9a-5d95-e211-a939-e4115bead28a')
    french_guiana = Constant('French Guiana', 'dbf682ac-5d95-e211-a939-e4115bead28a')
    french_polynesia = Constant('French Polynesia', 'dcf682ac-5d95-e211-a939-e4115bead28a')
    french_southern_territories = Constant(
        'French Southern Territories', 'ddf682ac-5d95-e211-a939-e4115bead28a'
    )
    gabon = Constant('Gabon', 'def682ac-5d95-e211-a939-e4115bead28a')
    gambia = Constant('Gambia, The', 'dff682ac-5d95-e211-a939-e4115bead28a')
    georgia = Constant('Georgia', 'e0f682ac-5d95-e211-a939-e4115bead28a')
    germany = Constant('Germany', '83756b9a-5d95-e211-a939-e4115bead28a')
    ghana = Constant('Ghana', 'e1f682ac-5d95-e211-a939-e4115bead28a')
    gibraltar = Constant('Gibraltar', 'e2f682ac-5d95-e211-a939-e4115bead28a')
    greece = Constant('Greece', 'e3f682ac-5d95-e211-a939-e4115bead28a')
    greenland = Constant('Greenland', 'e4f682ac-5d95-e211-a939-e4115bead28a')
    grenada = Constant('Grenada', 'e5f682ac-5d95-e211-a939-e4115bead28a')
    guadeloupe = Constant('Guadeloupe', 'e6f682ac-5d95-e211-a939-e4115bead28a')
    guam = Constant('Guam', 'e7f682ac-5d95-e211-a939-e4115bead28a')
    guatemala = Constant('Guatemala', 'e8f682ac-5d95-e211-a939-e4115bead28a')
    guernsey = Constant('Guernsey', '77756b9a-5d95-e211-a939-e4115bead28a')
    guinea = Constant('Guinea', 'e9f682ac-5d95-e211-a939-e4115bead28a')
    guinea_bissau = Constant('Guinea-Bissau', 'eaf682ac-5d95-e211-a939-e4115bead28a')
    guyana = Constant('Guyana', 'ebf682ac-5d95-e211-a939-e4115bead28a')
    haiti = Constant('Haiti', 'ecf682ac-5d95-e211-a939-e4115bead28a')
    heard_island_and_mcdonald_island = Constant('Heard Island and McDonald Island',
                                                'edf682ac-5d95-e211-a939-e4115bead28a')
    honduras = Constant('Honduras', 'eff682ac-5d95-e211-a939-e4115bead28a')
    hong_kong_sar = Constant('Hong Kong (SAR)', 'f0f682ac-5d95-e211-a939-e4115bead28a')
    hungary = Constant('Hungary', '6d6a9ab2-5d95-e211-a939-e4115bead28a')
    iceland = Constant('Iceland', '6e6a9ab2-5d95-e211-a939-e4115bead28a')
    india = Constant('India', '6f6a9ab2-5d95-e211-a939-e4115bead28a')
    indonesia = Constant('Indonesia', '706a9ab2-5d95-e211-a939-e4115bead28a')
    iran = Constant('Iran', '716a9ab2-5d95-e211-a939-e4115bead28a')
    iraq = Constant('Iraq', '726a9ab2-5d95-e211-a939-e4115bead28a')
    ireland = Constant('Ireland', '736a9ab2-5d95-e211-a939-e4115bead28a')
    isle_of_man = Constant('Isle of Man', '79756b9a-5d95-e211-a939-e4115bead28a')
    israel = Constant('Israel', '746a9ab2-5d95-e211-a939-e4115bead28a')
    italy = Constant('Italy', '84756b9a-5d95-e211-a939-e4115bead28a')
    ivory_coast = Constant('Ivory Coast', '756a9ab2-5d95-e211-a939-e4115bead28a')
    jamaica = Constant('Jamaica', '766a9ab2-5d95-e211-a939-e4115bead28a')
    japan = Constant('Japan', '85756b9a-5d95-e211-a939-e4115bead28a')
    jersey = Constant('Jersey', '78756b9a-5d95-e211-a939-e4115bead28a')
    jordan = Constant('Jordan', '776a9ab2-5d95-e211-a939-e4115bead28a')
    kazakhstan = Constant('Kazakhstan', '786a9ab2-5d95-e211-a939-e4115bead28a')
    kenya = Constant('Kenya', '796a9ab2-5d95-e211-a939-e4115bead28a')
    kiribati = Constant('Kiribati', '7a6a9ab2-5d95-e211-a939-e4115bead28a')
    korea_north = Constant('Korea (North)', '7b6a9ab2-5d95-e211-a939-e4115bead28a')
    korea_south = Constant('Korea (South)', '7c6a9ab2-5d95-e211-a939-e4115bead28a')
    kosovo = Constant('Kosovo', '7a756b9a-5d95-e211-a939-e4115bead28a')
    kuwait = Constant('Kuwait', '7d6a9ab2-5d95-e211-a939-e4115bead28a')
    kyrgyzstan = Constant('Kyrgyzstan', '7e6a9ab2-5d95-e211-a939-e4115bead28a')
    laos = Constant('Laos', '7f6a9ab2-5d95-e211-a939-e4115bead28a')
    latvia = Constant('Latvia', '806a9ab2-5d95-e211-a939-e4115bead28a')
    lebanon = Constant('Lebanon', '816a9ab2-5d95-e211-a939-e4115bead28a')
    lesotho = Constant('Lesotho', '826a9ab2-5d95-e211-a939-e4115bead28a')
    liberia = Constant('Liberia', '836a9ab2-5d95-e211-a939-e4115bead28a')
    libya = Constant('Libya', '846a9ab2-5d95-e211-a939-e4115bead28a')
    liechtenstein = Constant('Liechtenstein', '856a9ab2-5d95-e211-a939-e4115bead28a')
    lithuania = Constant('Lithuania', '866a9ab2-5d95-e211-a939-e4115bead28a')
    luxembourg = Constant('Luxembourg', '876a9ab2-5d95-e211-a939-e4115bead28a')
    macao_sar = Constant('Macao (SAR)', '886a9ab2-5d95-e211-a939-e4115bead28a')
    macedonia = Constant('Macedonia', '896a9ab2-5d95-e211-a939-e4115bead28a')
    madagascar = Constant('Madagascar', '0350bdb8-5d95-e211-a939-e4115bead28a')
    malawi = Constant('Malawi', '0450bdb8-5d95-e211-a939-e4115bead28a')
    malaysia = Constant('Malaysia', '0550bdb8-5d95-e211-a939-e4115bead28a')
    maldives = Constant('Maldives', '0650bdb8-5d95-e211-a939-e4115bead28a')
    mali = Constant('Mali', '0750bdb8-5d95-e211-a939-e4115bead28a')
    malta = Constant('Malta', '0850bdb8-5d95-e211-a939-e4115bead28a')
    marshall_islands = Constant('Marshall Islands', '0950bdb8-5d95-e211-a939-e4115bead28a')
    martinique = Constant('Martinique', '0a50bdb8-5d95-e211-a939-e4115bead28a')
    mauritania = Constant('Mauritania', '0b50bdb8-5d95-e211-a939-e4115bead28a')
    mauritius = Constant('Mauritius', '0c50bdb8-5d95-e211-a939-e4115bead28a')
    mayotte = Constant('Mayotte', '0d50bdb8-5d95-e211-a939-e4115bead28a')
    mexico = Constant('Mexico', '0e50bdb8-5d95-e211-a939-e4115bead28a')
    micronesia = Constant('Micronesia', '0f50bdb8-5d95-e211-a939-e4115bead28a')
    moldova = Constant('Moldova', '1050bdb8-5d95-e211-a939-e4115bead28a')
    monaco = Constant('Monaco', '1150bdb8-5d95-e211-a939-e4115bead28a')
    mongolia = Constant('Mongolia', '1250bdb8-5d95-e211-a939-e4115bead28a')
    montenegro = Constant('Montenegro', '7f756b9a-5d95-e211-a939-e4115bead28a')
    montserrat = Constant('Montserrat', '1350bdb8-5d95-e211-a939-e4115bead28a')
    morocco = Constant('Morocco', '1450bdb8-5d95-e211-a939-e4115bead28a')
    mozambique = Constant('Mozambique', '1550bdb8-5d95-e211-a939-e4115bead28a')
    namibia = Constant('Namibia', '1650bdb8-5d95-e211-a939-e4115bead28a')
    nauru = Constant('Nauru', '1750bdb8-5d95-e211-a939-e4115bead28a')
    nepal = Constant('Nepal', '1850bdb8-5d95-e211-a939-e4115bead28a')
    netherlands = Constant('Netherlands', '1950bdb8-5d95-e211-a939-e4115bead28a')
    netherlands_antilles = Constant('Netherlands Antilles', '1a50bdb8-5d95-e211-a939-e4115bead28a')
    new_caledonia = Constant('New Caledonia', '1b50bdb8-5d95-e211-a939-e4115bead28a')
    new_zealand = Constant('New Zealand', '1c50bdb8-5d95-e211-a939-e4115bead28a')
    nicaragua = Constant('Nicaragua', '1d50bdb8-5d95-e211-a939-e4115bead28a')
    niger = Constant('Niger', '4461b8be-5d95-e211-a939-e4115bead28a')
    nigeria = Constant('Nigeria', '4561b8be-5d95-e211-a939-e4115bead28a')
    niue = Constant('Niue', '4661b8be-5d95-e211-a939-e4115bead28a')
    norfolk_island = Constant('Norfolk Island', '4761b8be-5d95-e211-a939-e4115bead28a')
    northern_mariana_islands = Constant(
        'Northern Mariana Islands', '4861b8be-5d95-e211-a939-e4115bead28a'
    )
    norway = Constant('Norway', '4961b8be-5d95-e211-a939-e4115bead28a')
    occupied_palestinian_territories = Constant('Occupied Palestinian Territories',
                                                '35afd8d0-5d95-e211-a939-e4115bead28a')
    oman = Constant('Oman', '4a61b8be-5d95-e211-a939-e4115bead28a')
    pakistan = Constant('Pakistan', '4b61b8be-5d95-e211-a939-e4115bead28a')
    palau = Constant('Palau', '4c61b8be-5d95-e211-a939-e4115bead28a')
    panama = Constant('Panama', '4d61b8be-5d95-e211-a939-e4115bead28a')
    papua_new_guinea = Constant('Papua New Guinea', '4e61b8be-5d95-e211-a939-e4115bead28a')
    paraguay = Constant('Paraguay', '4f61b8be-5d95-e211-a939-e4115bead28a')
    peru = Constant('Peru', '5061b8be-5d95-e211-a939-e4115bead28a')
    philippines = Constant('Philippines', '5161b8be-5d95-e211-a939-e4115bead28a')
    pitcairn_henderson_ducie_and_oeno_islands = Constant(
        'Pitcairn, Henderson, Ducie and Oeno Islands', '5261b8be-5d95-e211-a939-e4115bead28a'
    )
    poland = Constant('Poland', '5361b8be-5d95-e211-a939-e4115bead28a')
    portugal = Constant('Portugal', '5461b8be-5d95-e211-a939-e4115bead28a')
    puerto_rico = Constant('Puerto Rico', '5561b8be-5d95-e211-a939-e4115bead28a')
    qatar = Constant('Qatar', '5661b8be-5d95-e211-a939-e4115bead28a')
    reunion = Constant('Reunion', '5761b8be-5d95-e211-a939-e4115bead28a')
    romania = Constant('Romania', '5861b8be-5d95-e211-a939-e4115bead28a')
    russia = Constant('Russia', '5961b8be-5d95-e211-a939-e4115bead28a')
    rwanda = Constant('Rwanda', '5a61b8be-5d95-e211-a939-e4115bead28a')
    samoa = Constant('Samoa', '5b61b8be-5d95-e211-a939-e4115bead28a')
    san_marino = Constant('San Marino', '5c61b8be-5d95-e211-a939-e4115bead28a')
    sao_tome_and_principe = Constant(
        'Sao Tome and Principe', '5d61b8be-5d95-e211-a939-e4115bead28a'
    )
    saudi_arabia = Constant('Saudi Arabia', '1a0be5c4-5d95-e211-a939-e4115bead28a')
    senegal = Constant('Senegal', '1b0be5c4-5d95-e211-a939-e4115bead28a')
    serbia = Constant('Serbia', '1c0be5c4-5d95-e211-a939-e4115bead28a')
    seychelles = Constant('Seychelles', '1d0be5c4-5d95-e211-a939-e4115bead28a')
    sierra_leone = Constant('Sierra Leone', '1e0be5c4-5d95-e211-a939-e4115bead28a')
    singapore = Constant('Singapore', '1f0be5c4-5d95-e211-a939-e4115bead28a')
    slovakia = Constant('Slovakia', '200be5c4-5d95-e211-a939-e4115bead28a')
    slovenia = Constant('Slovenia', '210be5c4-5d95-e211-a939-e4115bead28a')
    solomon_islands = Constant('Solomon Islands', '220be5c4-5d95-e211-a939-e4115bead28a')
    somalia = Constant('Somalia', '230be5c4-5d95-e211-a939-e4115bead28a')
    south_africa = Constant('South Africa', '240be5c4-5d95-e211-a939-e4115bead28a')
    south_georgia_and_south_sandwich_islands = Constant('South Georgia and South Sandwich Islands',
                                                        '250be5c4-5d95-e211-a939-e4115bead28a')
    spain = Constant('Spain', '86756b9a-5d95-e211-a939-e4115bead28a')
    sri_lanka = Constant('Sri Lanka', '260be5c4-5d95-e211-a939-e4115bead28a')
    st_barthelemy = Constant('St Barthelemy', '7b756b9a-5d95-e211-a939-e4115bead28a')
    st_helena = Constant('St Helena', '270be5c4-5d95-e211-a939-e4115bead28a')
    st_kitts_and_nevis = Constant('St Kitts and Nevis', '280be5c4-5d95-e211-a939-e4115bead28a')
    st_lucia = Constant('St Lucia', '290be5c4-5d95-e211-a939-e4115bead28a')
    st_martin = Constant('St Martin', '7c756b9a-5d95-e211-a939-e4115bead28a')
    st_pierre_and_miquelon = Constant(
        'St Pierre and Miquelon', '2a0be5c4-5d95-e211-a939-e4115bead28a'
    )
    st_vincent = Constant('St Vincent', '2b0be5c4-5d95-e211-a939-e4115bead28a')
    sudan = Constant('Sudan', '2c0be5c4-5d95-e211-a939-e4115bead28a')
    sudan_south = Constant('Sudan, South', '7e756b9a-5d95-e211-a939-e4115bead28a')
    surinam = Constant('Surinam', '2d0be5c4-5d95-e211-a939-e4115bead28a')
    svalbard_and_jan_mayen_islands = Constant(
        'Svalbard and Jan Mayen Islands', '2e0be5c4-5d95-e211-a939-e4115bead28a'
    )
    swaziland = Constant('Swaziland', '2f0be5c4-5d95-e211-a939-e4115bead28a')
    sweden = Constant('Sweden', '300be5c4-5d95-e211-a939-e4115bead28a')
    switzerland = Constant('Switzerland', '310be5c4-5d95-e211-a939-e4115bead28a')
    syria = Constant('Syria', 'a46ee1ca-5d95-e211-a939-e4115bead28a')
    taiwan = Constant('Taiwan', 'a56ee1ca-5d95-e211-a939-e4115bead28a')
    tajikistan = Constant('Tajikistan', 'a66ee1ca-5d95-e211-a939-e4115bead28a')
    tanzania = Constant('Tanzania', 'a76ee1ca-5d95-e211-a939-e4115bead28a')
    thailand = Constant('Thailand', 'a86ee1ca-5d95-e211-a939-e4115bead28a')
    togo = Constant('Togo', 'a96ee1ca-5d95-e211-a939-e4115bead28a')
    tokelau = Constant('Tokelau', 'aa6ee1ca-5d95-e211-a939-e4115bead28a')
    tonga = Constant('Tonga', 'ab6ee1ca-5d95-e211-a939-e4115bead28a')
    trinidad_and_tobago = Constant('Trinidad and Tobago', 'ac6ee1ca-5d95-e211-a939-e4115bead28a')
    tunisia = Constant('Tunisia', 'ad6ee1ca-5d95-e211-a939-e4115bead28a')
    turkey = Constant('Turkey', 'ae6ee1ca-5d95-e211-a939-e4115bead28a')
    turkmenistan = Constant('Turkmenistan', 'af6ee1ca-5d95-e211-a939-e4115bead28a')
    turks_and_caicos_islands = Constant(
        'Turks and Caicos Islands', 'b06ee1ca-5d95-e211-a939-e4115bead28a'
    )
    tuvalu = Constant('Tuvalu', 'b16ee1ca-5d95-e211-a939-e4115bead28a')
    uganda = Constant('Uganda', 'b26ee1ca-5d95-e211-a939-e4115bead28a')
    ukraine = Constant('Ukraine', 'b36ee1ca-5d95-e211-a939-e4115bead28a')
    united_arab_emirates = Constant('United Arab Emirates', 'b46ee1ca-5d95-e211-a939-e4115bead28a')
    united_kingdom = Constant('United Kingdom', '80756b9a-5d95-e211-a939-e4115bead28a')
    united_states = Constant('United States', '81756b9a-5d95-e211-a939-e4115bead28a')
    united_states_minor_outlying_islands = Constant('United States Minor Outlying Islands',
                                                    'b56ee1ca-5d95-e211-a939-e4115bead28a')
    uruguay = Constant('Uruguay', 'b66ee1ca-5d95-e211-a939-e4115bead28a')
    uzbekistan = Constant('Uzbekistan', 'b76ee1ca-5d95-e211-a939-e4115bead28a')
    vanuatu = Constant('Vanuatu', 'b86ee1ca-5d95-e211-a939-e4115bead28a')
    vatican_city = Constant('Vatican City', 'eef682ac-5d95-e211-a939-e4115bead28a')
    venezuela = Constant('Venezuela', 'b96ee1ca-5d95-e211-a939-e4115bead28a')
    vietnam = Constant('Vietnam', 'ba6ee1ca-5d95-e211-a939-e4115bead28a')
    virgin_islands = Constant('Virgin Islands (US)', 'bb6ee1ca-5d95-e211-a939-e4115bead28a')
    wallis_and_futuna = Constant('Wallis and Futuna', '34afd8d0-5d95-e211-a939-e4115bead28a')
    western_sahara = Constant('Western Sahara', '36afd8d0-5d95-e211-a939-e4115bead28a')
    yemen = Constant('Yemen', '37afd8d0-5d95-e211-a939-e4115bead28a')
    zambia = Constant('Zambia', '38afd8d0-5d95-e211-a939-e4115bead28a')
    zimbabwe = Constant('Zimbabwe', '39afd8d0-5d95-e211-a939-e4115bead28a')


class Sector(Enum):
    """Sectors (not all of them!)."""

    aerospace_assembly_aircraft = Constant(
        'Aerospace : Manufacturing and Assembly : Aircraft',
        'b422c9d2-5f95-e211-a939-e4115bead28a'
    )
    renewable_energy_wind = Constant(
        'Renewable Energy : Wind',
        'a4959812-6095-e211-a939-e4115bead28a'
    )


class Title(Enum):
    """Titles."""

    admiral = Constant('Admiral', 'c1d9b924-6095-e211-a939-e4115bead28a')
    admiral_of_the_fleet = Constant('Admiral of the Fleet', 'c2d9b924-6095-e211-a939-e4115bead28a')
    air_chief_marshal = Constant('Air Chief Marshal', 'c3d9b924-6095-e211-a939-e4115bead28a')
    air_commodore = Constant('Air Commodore', 'c4d9b924-6095-e211-a939-e4115bead28a')
    air_marshal = Constant('Air Marshal', 'c5d9b924-6095-e211-a939-e4115bead28a')
    air_vice_marshal = Constant('Air Vice-Marshal', 'c6d9b924-6095-e211-a939-e4115bead28a')
    baroness = Constant('Baroness', 'bed9b924-6095-e211-a939-e4115bead28a')
    brigadier = Constant('Brigadier', 'c7d9b924-6095-e211-a939-e4115bead28a')
    captain = Constant('Captain', 'c8d9b924-6095-e211-a939-e4115bead28a')
    colonel = Constant('Colonel', 'c9d9b924-6095-e211-a939-e4115bead28a')
    commander = Constant('Commander', 'cad9b924-6095-e211-a939-e4115bead28a')
    commodore = Constant('Commodore', 'cbd9b924-6095-e211-a939-e4115bead28a')
    corporal = Constant('Corporal', 'f4c5716b-1770-e411-a72b-e4115bead28a')
    dame = Constant('Dame', 'bad9b924-6095-e211-a939-e4115bead28a')
    dr = Constant('Dr', 'b5d9b924-6095-e211-a939-e4115bead28a')
    field_marshal = Constant('Field Marshal', 'ccd9b924-6095-e211-a939-e4115bead28a')
    flight_lieutenant = Constant('Flight Lieutenant', 'cdd9b924-6095-e211-a939-e4115bead28a')
    flying_officer = Constant('Flying Officer', 'ced9b924-6095-e211-a939-e4115bead28a')
    general = Constant('General', 'cfd9b924-6095-e211-a939-e4115bead28a')
    group_captain = Constant('Group Captain', 'd0d9b924-6095-e211-a939-e4115bead28a')
    he = Constant('HE', 'bfd9b924-6095-e211-a939-e4115bead28a')
    hrh = Constant('HRH', 'c0d9b924-6095-e211-a939-e4115bead28a')
    lady = Constant('Lady', 'b8d9b924-6095-e211-a939-e4115bead28a')
    lieutenant = Constant('Lieutenant', 'd1d9b924-6095-e211-a939-e4115bead28a')
    lieutenant_colonel = Constant('Lieutenant Colonel', 'd3d9b924-6095-e211-a939-e4115bead28a')
    lieutenant_commander = Constant('Lieutenant Commander', 'd2d9b924-6095-e211-a939-e4115bead28a')
    lieutenant_general = Constant('Lieutenant General', 'd4d9b924-6095-e211-a939-e4115bead28a')
    lord = Constant('Lord', 'b9d9b924-6095-e211-a939-e4115bead28a')
    major = Constant('Major', 'd5d9b924-6095-e211-a939-e4115bead28a')
    major_general = Constant('Major General', 'd6d9b924-6095-e211-a939-e4115bead28a')
    marshal_of_the_raf = Constant('Marshal of the RAF', 'd7d9b924-6095-e211-a939-e4115bead28a')
    miss = Constant('Miss', 'a46cb21e-6095-e211-a939-e4115bead28a')
    mr = Constant('Mr', 'a26cb21e-6095-e211-a939-e4115bead28a')
    mrs = Constant('Mrs', 'a36cb21e-6095-e211-a939-e4115bead28a')
    ms = Constant('Ms', 'b4d9b924-6095-e211-a939-e4115bead28a')
    pilot_officer = Constant('Pilot Officer', 'd8d9b924-6095-e211-a939-e4115bead28a')
    professor = Constant('Professor', 'bbd9b924-6095-e211-a939-e4115bead28a')
    rear_admiral = Constant('Rear Admiral', 'd9d9b924-6095-e211-a939-e4115bead28a')
    reverend = Constant('Reverend', 'b6d9b924-6095-e211-a939-e4115bead28a')
    second_lieutenant = Constant('Second Lieutenant', 'dad9b924-6095-e211-a939-e4115bead28a')
    sir = Constant('Sir', 'b7d9b924-6095-e211-a939-e4115bead28a')
    squadron_leader = Constant('Squadron Leader', 'dbd9b924-6095-e211-a939-e4115bead28a')
    sub_lieutenant = Constant('Sub-Lieutenant', '744cd12a-6095-e211-a939-e4115bead28a')
    the_hon = Constant('The Hon', 'bcd9b924-6095-e211-a939-e4115bead28a')
    the_rt_hon = Constant('The Rt Hon', 'bdd9b924-6095-e211-a939-e4115bead28a')
    vice_admiral = Constant('Vice Admiral', '754cd12a-6095-e211-a939-e4115bead28a')
    wing_commander = Constant('Wing Commander', '764cd12a-6095-e211-a939-e4115bead28a')


class UKRegion(Enum):
    """UK Regions."""

    alderney = Constant('Alderney', '934cd12a-6095-e211-a939-e4115bead28a')
    all = Constant('All', '1718e330-6095-e211-a939-e4115bead28a')
    channel_islands = Constant('Channel Islands', '8b4cd12a-6095-e211-a939-e4115bead28a')
    east_midlands = Constant('East Midlands', '844cd12a-6095-e211-a939-e4115bead28a')
    east_of_england = Constant('East of England', '864cd12a-6095-e211-a939-e4115bead28a')
    england = Constant('England', '8a4cd12a-6095-e211-a939-e4115bead28a')
    fdi_hub = Constant('FDI Hub', '804cd12a-6095-e211-a939-e4115bead28a')
    guernsey = Constant('Guernsey', '904cd12a-6095-e211-a939-e4115bead28a')
    isle_of_man = Constant('Isle of Man', '8f4cd12a-6095-e211-a939-e4115bead28a')
    jersey = Constant('Jersey', '924cd12a-6095-e211-a939-e4115bead28a')
    london = Constant('London', '874cd12a-6095-e211-a939-e4115bead28a')
    north_east = Constant('North East', '814cd12a-6095-e211-a939-e4115bead28a')
    northern_ireland = Constant('Northern Ireland', '8e4cd12a-6095-e211-a939-e4115bead28a')
    north_west = Constant('North West', '824cd12a-6095-e211-a939-e4115bead28a')
    sark = Constant('Sark', '914cd12a-6095-e211-a939-e4115bead28a')
    scotland = Constant('Scotland', '8c4cd12a-6095-e211-a939-e4115bead28a')
    south_east = Constant('South East', '884cd12a-6095-e211-a939-e4115bead28a')
    south_west = Constant('South West', '894cd12a-6095-e211-a939-e4115bead28a')
    ukti_dubai_hub = Constant('UKTI Dubai Hub', 'e1dd40e9-3dfd-e311-8a2b-e4115bead28a')
    wales = Constant('Wales', '8d4cd12a-6095-e211-a939-e4115bead28a')
    west_midlands = Constant('West Midlands', '854cd12a-6095-e211-a939-e4115bead28a')
    yorkshire_and_the_humber = Constant(
        'Yorkshire and The Humber', '834cd12a-6095-e211-a939-e4115bead28a'
    )


class Service(Enum):
    """Service."""

    trade_enquiry = Constant('Trade - Enquiry', '330bba2b-3499-e211-a939-e4115bead28a')
    account_management = Constant('Account Management', '9484b82b-3499-e211-a939-e4115bead28a')


class Team(Enum):
    """Team."""

    healthcare_uk = Constant('Healthcare UK', '3ff47a07-002c-e311-a78e-e4115bead28a')
    tees_valley_lep = Constant('Tees Valley LEP', 'a889ef76-8925-e511-b6bc-e4115bead28a')
    td_events_healthcare = Constant(
        'TD - Events - Healthcare', 'daf924aa-9698-e211-a939-e4115bead28a'
    )
    food_from_britain = Constant('Food From Britain', '8cf924aa-9698-e211-a939-e4115bead28a')
    crm = Constant('crm', 'a7f924aa-9698-e211-a939-e4115bead28a')


class HeadquarterType(Enum):
    """Headquarter type."""

    ukhq = Constant('ukhq', '3e6debb4-1596-40c5-aa25-f00da0e05af9')
    ehq = Constant('ehq', 'eb59eaeb-eeb8-4f54-9506-a5e08773046b')
    ghq = Constant('ghq', '43281c5e-92a4-4794-867b-b4d5f801e6f3')


class EmployeeRange(Enum):
    """Employee range constants."""

    range_1_to_9 = Constant('1 to 9', '3dafd8d0-5d95-e211-a939-e4115bead28a')
    range_10_to_49 = Constant('10 to 49', '3eafd8d0-5d95-e211-a939-e4115bead28a')
    range_50_to_249 = Constant('50 to 249', '3fafd8d0-5d95-e211-a939-e4115bead28a')
    range_250_to_499 = Constant('250 to 499', '40afd8d0-5d95-e211-a939-e4115bead28a')
    range_500_plus = Constant('500+', '41afd8d0-5d95-e211-a939-e4115bead28a')


class TurnoverRange(Enum):
    """Turnover range constants."""

    range_0_to_1_34 = Constant('£0 ti £1.34M', '774cd12a-6095-e211-a939-e4115bead28a')
    range_1_34_to_6_7 = Constant('£1.34 to £6.7M', '784cd12a-6095-e211-a939-e4115bead28a')
    range_6_7_to_33_5 = Constant('£6.7 to £33.5M', '794cd12a-6095-e211-a939-e4115bead28a')
    range_33_5_plus = Constant('£33.5M+', '7a4cd12a-6095-e211-a939-e4115bead28a')


class InvestmentProjectStage(Enum):
    """Investment project stage constants."""

    prospect = OrderedConstant(
        'Prospect', '8a320cc9-ae2e-443e-9d26-2f36452c2ced', 200.0
    )
    assign_pm = OrderedConstant(
        'Assign PM', 'c9864359-fb1a-4646-a4c1-97d10189fc03', 300.0
    )
    active = OrderedConstant(
        'Active', '7606cc19-20da-4b74-aba1-2cec0d753ad8', 400.0
    )
    verify_win = OrderedConstant(
        'Verify win', '49b8f6f3-0c50-4150-a965-2c974f3149e3', 500.0
    )
    won = OrderedConstant('Won', '945ea6d1-eee3-4f5b-9144-84a75b71b8e6', 600.0)


class InvestmentType(Enum):
    """Investment type constants."""

    fdi = Constant('FDI', '3e143372-496c-4d1e-8278-6fdd3da9b48b')
    non_fdi = Constant('Non-FDI', '9c364e64-2b28-401b-b2df-50e08b0bca44')
    commitment_to_invest = Constant('Commitment to invest',
                                    '031269ab-b7ec-40e9-8a4e-7371404f0622')


class ReferralSourceActivity(Enum):
    """Referral source activity constants."""

    cold_call = Constant(
        'Cold call', '0c4f8e74-d34f-4aca-b764-a44cdc2d0087'
    )
    direct_enquiry = Constant(
        'Direct enquiry', '7d98f3a6-3e3f-40ac-a6f3-3f0c251ec1d2'
    )
    event = Constant(
        'Event', '3816a95b-6a76-4ad0-8ae9-b0d7e7d2b79c'
    )
    marketing = Constant(
        'Marketing', '0acf0e68-e09e-4e5d-92b6-e72e5a5c7ea4'
    )
    multiplier = Constant(
        'Multiplier', 'e95cddb3-9407-4c8a-b5a6-2616117b0aae'
    )
    none = Constant(
        'None', 'aba8f653-264f-48d8-950e-07f9c418c7b0'
    )
    other = Constant(
        'Other', '318e6e9e-2a0e-4e4b-a495-c48aeee4b996'
    )
    relationship_management_activity = Constant(
        'Relationship management activity',
        '668e999c-a669-4d9b-bfbf-6275ceed86da'
    )
    personal_reference = Constant(
        'Personal reference', 'c03c4043-18b4-4463-a36b-a1af1b35f95d'
    )
    website = Constant(
        'Website', '812b2f62-fe62-4cc8-b69c-58f3e2ebac17'
    )


class InvestmentBusinessActivity(Enum):
    """Investment business activity constants."""

    retail = Constant('Retail', 'a2dbd807-ae52-421c-8d1d-88adfc7a506b')
    other = Constant('Other', 'befab707-5abd-4f47-8477-57f091e6dac9')


class FDIType(Enum):
    """Investment FDI type constants."""

    creation_of_new_site_or_activity = Constant(
        'Creation of new site or activity',
        'f8447013-cfdc-4f35-a146-6619665388b3'
    )


class FDIValue(Enum):
    """Investment FDI value constants."""

    higher = Constant(
        'Higher', '38e36c77-61ad-4186-a7a8-ac6a1a1104c6'
    )


class SalaryRange(Enum):
    """Average salary constants."""

    below_25000 = OrderedConstant(
        'Below £25,000', '2943bf3d-32dd-43be-8ad4-969b006dee7b', 100.0
    )


class InvestmentStrategicDriver(Enum):
    """Investment strategic driver constants."""

    access_to_market = Constant(
        'Access to market', '382aa6d1-a362-4166-a09d-f579d9f3be75'
    )

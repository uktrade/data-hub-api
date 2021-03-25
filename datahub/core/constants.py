from collections import namedtuple
from enum import Enum

Constant = namedtuple('Constant', ('name', 'id'))
OrderedConstant = namedtuple('OrderedConstant', ('name', 'id', 'order'))
CountryConstant = namedtuple(
    'CountryConstant',
    (
        'name',
        'id',
        'postcode_pattern',
        'postcode_replacement',
    ),
)

US_ZIP_STATES = (
    ('005', 'NY', 'New York'),
    ('006', 'PR', 'Puerto Rico'),
    ('007', 'PR', 'Puerto Rico'),
    ('009', 'PR', 'Puerto Rico'),
    ('010', 'MA', 'Massachusetts'),
    ('011', 'MA', 'Massachusetts'),
    ('012', 'MA', 'Massachusetts'),
    ('013', 'MA', 'Massachusetts'),
    ('014', 'MA', 'Massachusetts'),
    ('015', 'MA', 'Massachusetts'),
    ('016', 'MA', 'Massachusetts'),
    ('017', 'MA', 'Massachusetts'),
    ('018', 'MA', 'Massachusetts'),
    ('019', 'MA', 'Massachusetts'),
    ('020', 'MA', 'Massachusetts'),
    ('021', 'MA', 'Massachusetts'),
    ('022', 'MA', 'Massachusetts'),
    ('023', 'MA', 'Massachusetts'),
    ('024', 'MA', 'Massachusetts'),
    ('025', 'MA', 'Massachusetts'),
    ('026', 'MA', 'Massachusetts'),
    ('027', 'MA', 'Massachusetts'),
    ('028', 'RI', 'Rhode Island'),
    ('029', 'RI', 'Rhode Island'),
    ('030', 'NH', 'New Hampshire'),
    ('031', 'NH', 'New Hampshire'),
    ('032', 'NH', 'New Hampshire'),
    ('033', 'NH', 'New Hampshire'),
    ('034', 'NH', 'New Hampshire'),
    ('035', 'NH', 'New Hampshire'),
    ('036', 'NH', 'New Hampshire'),
    ('037', 'NH', 'New Hampshire'),
    ('038', 'NH', 'New Hampshire'),
    ('039', 'ME', 'Maine'),
    ('040', 'ME', 'Maine'),
    ('041', 'ME', 'Maine'),
    ('042', 'ME', 'Maine'),
    ('043', 'ME', 'Maine'),
    ('044', 'ME', 'Maine'),
    ('045', 'ME', 'Maine'),
    ('046', 'ME', 'Maine'),
    ('047', 'ME', 'Maine'),
    ('048', 'ME', 'Maine'),
    ('049', 'ME', 'Maine'),
    ('050', 'VT', 'Vermont'),
    ('051', 'VT', 'Vermont'),
    ('052', 'VT', 'Vermont'),
    ('053', 'VT', 'Vermont'),
    ('054', 'VT', 'Vermont'),
    ('055', 'MA', 'Massachusetts'),
    ('056', 'VT', 'Vermont'),
    ('057', 'VT', 'Vermont'),
    ('058', 'VT', 'Vermont'),
    ('059', 'VT', 'Vermont'),
    ('060', 'CT', 'Connecticut'),
    ('061', 'CT', 'Connecticut'),
    ('062', 'CT', 'Connecticut'),
    ('063', 'CT', 'Connecticut'),
    ('064', 'CT', 'Connecticut'),
    ('065', 'CT', 'Connecticut'),
    ('066', 'CT', 'Connecticut'),
    ('067', 'CT', 'Connecticut'),
    ('068', 'CT', 'Connecticut'),
    ('069', 'CT', 'Connecticut'),
    ('070', 'NJ', 'New Jersey'),
    ('071', 'NJ', 'New Jersey'),
    ('072', 'NJ', 'New Jersey'),
    ('073', 'NJ', 'New Jersey'),
    ('074', 'NJ', 'New Jersey'),
    ('075', 'NJ', 'New Jersey'),
    ('076', 'NJ', 'New Jersey'),
    ('077', 'NJ', 'New Jersey'),
    ('078', 'NJ', 'New Jersey'),
    ('079', 'NJ', 'New Jersey'),
    ('080', 'NJ', 'New Jersey'),
    ('081', 'NJ', 'New Jersey'),
    ('082', 'NJ', 'New Jersey'),
    ('083', 'NJ', 'New Jersey'),
    ('084', 'NJ', 'New Jersey'),
    ('085', 'NJ', 'New Jersey'),
    ('086', 'NJ', 'New Jersey'),
    ('087', 'NJ', 'New Jersey'),
    ('088', 'NJ', 'New Jersey'),
    ('089', 'NJ', 'New Jersey'),
    ('100', 'NY', 'New York'),
    ('101', 'NY', 'New York'),
    ('102', 'NY', 'New York'),
    ('103', 'NY', 'New York'),
    ('104', 'NY', 'New York'),
    ('105', 'NY', 'New York'),
    ('106', 'NY', 'New York'),
    ('107', 'NY', 'New York'),
    ('108', 'NY', 'New York'),
    ('109', 'NY', 'New York'),
    ('110', 'NY', 'New York'),
    ('111', 'NY', 'New York'),
    ('112', 'NY', 'New York'),
    ('113', 'NY', 'New York'),
    ('114', 'NY', 'New York'),
    ('115', 'NY', 'New York'),
    ('116', 'NY', 'New York'),
    ('117', 'NY', 'New York'),
    ('118', 'NY', 'New York'),
    ('119', 'NY', 'New York'),
    ('120', 'NY', 'New York'),
    ('121', 'NY', 'New York'),
    ('122', 'NY', 'New York'),
    ('123', 'NY', 'New York'),
    ('124', 'NY', 'New York'),
    ('125', 'NY', 'New York'),
    ('126', 'NY', 'New York'),
    ('127', 'NY', 'New York'),
    ('128', 'NY', 'New York'),
    ('129', 'NY', 'New York'),
    ('130', 'NY', 'New York'),
    ('131', 'NY', 'New York'),
    ('132', 'NY', 'New York'),
    ('133', 'NY', 'New York'),
    ('134', 'NY', 'New York'),
    ('135', 'NY', 'New York'),
    ('136', 'NY', 'New York'),
    ('137', 'NY', 'New York'),
    ('138', 'NY', 'New York'),
    ('139', 'NY', 'New York'),
    ('140', 'NY', 'New York'),
    ('141', 'NY', 'New York'),
    ('142', 'NY', 'New York'),
    ('143', 'NY', 'New York'),
    ('144', 'NY', 'New York'),
    ('145', 'NY', 'New York'),
    ('146', 'NY', 'New York'),
    ('147', 'NY', 'New York'),
    ('148', 'NY', 'New York'),
    ('149', 'NY', 'New York'),
    ('150', 'PA', 'Pennsylvania'),
    ('151', 'PA', 'Pennsylvania'),
    ('152', 'PA', 'Pennsylvania'),
    ('153', 'PA', 'Pennsylvania'),
    ('154', 'PA', 'Pennsylvania'),
    ('155', 'PA', 'Pennsylvania'),
    ('156', 'PA', 'Pennsylvania'),
    ('157', 'PA', 'Pennsylvania'),
    ('158', 'PA', 'Pennsylvania'),
    ('159', 'PA', 'Pennsylvania'),
    ('160', 'PA', 'Pennsylvania'),
    ('161', 'PA', 'Pennsylvania'),
    ('162', 'PA', 'Pennsylvania'),
    ('163', 'PA', 'Pennsylvania'),
    ('164', 'PA', 'Pennsylvania'),
    ('165', 'PA', 'Pennsylvania'),
    ('166', 'PA', 'Pennsylvania'),
    ('167', 'PA', 'Pennsylvania'),
    ('168', 'PA', 'Pennsylvania'),
    ('169', 'PA', 'Pennsylvania'),
    ('170', 'PA', 'Pennsylvania'),
    ('171', 'PA', 'Pennsylvania'),
    ('172', 'PA', 'Pennsylvania'),
    ('173', 'PA', 'Pennsylvania'),
    ('174', 'PA', 'Pennsylvania'),
    ('175', 'PA', 'Pennsylvania'),
    ('176', 'PA', 'Pennsylvania'),
    ('177', 'PA', 'Pennsylvania'),
    ('178', 'PA', 'Pennsylvania'),
    ('179', 'PA', 'Pennsylvania'),
    ('180', 'PA', 'Pennsylvania'),
    ('181', 'PA', 'Pennsylvania'),
    ('182', 'PA', 'Pennsylvania'),
    ('183', 'PA', 'Pennsylvania'),
    ('184', 'PA', 'Pennsylvania'),
    ('185', 'PA', 'Pennsylvania'),
    ('186', 'PA', 'Pennsylvania'),
    ('187', 'PA', 'Pennsylvania'),
    ('188', 'PA', 'Pennsylvania'),
    ('189', 'PA', 'Pennsylvania'),
    ('190', 'PA', 'Pennsylvania'),
    ('191', 'PA', 'Pennsylvania'),
    ('193', 'PA', 'Pennsylvania'),
    ('194', 'PA', 'Pennsylvania'),
    ('195', 'PA', 'Pennsylvania'),
    ('196', 'PA', 'Pennsylvania'),
    ('197', 'DE', 'Delaware'),
    ('198', 'DE', 'Delaware'),
    ('199', 'DE', 'Delaware'),
    ('200', 'DC', 'District of Columbia'),
    ('201', 'VA', 'Virginia'),
    ('202', 'DC', 'District of Columbia'),
    ('203', 'DC', 'District of Columbia'),
    ('204', 'DC', 'District of Columbia'),
    ('205', 'DC', 'District of Columbia'),
    ('206', 'MD', 'Maryland'),
    ('207', 'MD', 'Maryland'),
    ('208', 'MD', 'Maryland'),
    ('209', 'MD', 'Maryland'),
    ('210', 'MD', 'Maryland'),
    ('211', 'MD', 'Maryland'),
    ('212', 'MD', 'Maryland'),
    ('214', 'MD', 'Maryland'),
    ('215', 'MD', 'Maryland'),
    ('216', 'MD', 'Maryland'),
    ('217', 'MD', 'Maryland'),
    ('218', 'MD', 'Maryland'),
    ('219', 'MD', 'Maryland'),
    ('220', 'VA', 'Virginia'),
    ('221', 'VA', 'Virginia'),
    ('222', 'VA', 'Virginia'),
    ('223', 'VA', 'Virginia'),
    ('224', 'VA', 'Virginia'),
    ('225', 'VA', 'Virginia'),
    ('226', 'VA', 'Virginia'),
    ('227', 'VA', 'Virginia'),
    ('228', 'VA', 'Virginia'),
    ('229', 'VA', 'Virginia'),
    ('230', 'VA', 'Virginia'),
    ('231', 'VA', 'Virginia'),
    ('232', 'VA', 'Virginia'),
    ('233', 'VA', 'Virginia'),
    ('234', 'VA', 'Virginia'),
    ('235', 'VA', 'Virginia'),
    ('236', 'VA', 'Virginia'),
    ('237', 'VA', 'Virginia'),
    ('238', 'VA', 'Virginia'),
    ('239', 'VA', 'Virginia'),
    ('240', 'VA', 'Virginia'),
    ('241', 'VA', 'Virginia'),
    ('242', 'VA', 'Virginia'),
    ('243', 'VA', 'Virginia'),
    ('244', 'VA', 'Virginia'),
    ('245', 'VA', 'Virginia'),
    ('246', 'VA', 'Virginia'),
    ('247', 'WV', 'West Virginia'),
    ('248', 'WV', 'West Virginia'),
    ('249', 'WV', 'West Virginia'),
    ('250', 'WV', 'West Virginia'),
    ('251', 'WV', 'West Virginia'),
    ('252', 'WV', 'West Virginia'),
    ('253', 'WV', 'West Virginia'),
    ('254', 'WV', 'West Virginia'),
    ('255', 'WV', 'West Virginia'),
    ('256', 'WV', 'West Virginia'),
    ('257', 'WV', 'West Virginia'),
    ('258', 'WV', 'West Virginia'),
    ('259', 'WV', 'West Virginia'),
    ('260', 'WV', 'West Virginia'),
    ('261', 'WV', 'West Virginia'),
    ('262', 'WV', 'West Virginia'),
    ('263', 'WV', 'West Virginia'),
    ('264', 'WV', 'West Virginia'),
    ('265', 'WV', 'West Virginia'),
    ('266', 'WV', 'West Virginia'),
    ('267', 'WV', 'West Virginia'),
    ('268', 'WV', 'West Virginia'),
    ('270', 'NC', 'North Carolina'),
    ('271', 'NC', 'North Carolina'),
    ('272', 'NC', 'North Carolina'),
    ('273', 'NC', 'North Carolina'),
    ('274', 'NC', 'North Carolina'),
    ('275', 'NC', 'North Carolina'),
    ('276', 'NC', 'North Carolina'),
    ('277', 'NC', 'North Carolina'),
    ('278', 'NC', 'North Carolina'),
    ('279', 'NC', 'North Carolina'),
    ('280', 'NC', 'North Carolina'),
    ('281', 'NC', 'North Carolina'),
    ('282', 'NC', 'North Carolina'),
    ('283', 'NC', 'North Carolina'),
    ('284', 'NC', 'North Carolina'),
    ('285', 'NC', 'North Carolina'),
    ('286', 'NC', 'North Carolina'),
    ('287', 'NC', 'North Carolina'),
    ('288', 'NC', 'North Carolina'),
    ('289', 'NC', 'North Carolina'),
    ('290', 'SC', 'South Carolina'),
    ('291', 'SC', 'South Carolina'),
    ('292', 'SC', 'South Carolina'),
    ('293', 'SC', 'South Carolina'),
    ('294', 'SC', 'South Carolina'),
    ('295', 'SC', 'South Carolina'),
    ('296', 'SC', 'South Carolina'),
    ('297', 'SC', 'South Carolina'),
    ('298', 'SC', 'South Carolina'),
    ('299', 'SC', 'South Carolina'),
    ('300', 'GA', 'Georgia'),
    ('301', 'GA', 'Georgia'),
    ('302', 'GA', 'Georgia'),
    ('303', 'GA', 'Georgia'),
    ('304', 'GA', 'Georgia'),
    ('305', 'GA', 'Georgia'),
    ('306', 'GA', 'Georgia'),
    ('307', 'GA', 'Georgia'),
    ('308', 'GA', 'Georgia'),
    ('309', 'GA', 'Georgia'),
    ('310', 'GA', 'Georgia'),
    ('311', 'GA', 'Georgia'),
    ('312', 'GA', 'Georgia'),
    ('313', 'GA', 'Georgia'),
    ('314', 'GA', 'Georgia'),
    ('315', 'GA', 'Georgia'),
    ('316', 'GA', 'Georgia'),
    ('317', 'GA', 'Georgia'),
    ('318', 'GA', 'Georgia'),
    ('319', 'GA', 'Georgia'),
    ('320', 'FL', 'Florida'),
    ('321', 'FL', 'Florida'),
    ('322', 'FL', 'Florida'),
    ('323', 'FL', 'Florida'),
    ('324', 'FL', 'Florida'),
    ('325', 'FL', 'Florida'),
    ('326', 'FL', 'Florida'),
    ('327', 'FL', 'Florida'),
    ('328', 'FL', 'Florida'),
    ('329', 'FL', 'Florida'),
    ('330', 'FL', 'Florida'),
    ('331', 'FL', 'Florida'),
    ('332', 'FL', 'Florida'),
    ('333', 'FL', 'Florida'),
    ('334', 'FL', 'Florida'),
    ('335', 'FL', 'Florida'),
    ('336', 'FL', 'Florida'),
    ('337', 'FL', 'Florida'),
    ('338', 'FL', 'Florida'),
    ('339', 'FL', 'Florida'),
    ('341', 'FL', 'Florida'),
    ('342', 'FL', 'Florida'),
    ('344', 'FL', 'Florida'),
    ('346', 'FL', 'Florida'),
    ('347', 'FL', 'Florida'),
    ('349', 'FL', 'Florida'),
    ('350', 'AL', 'Alabama'),
    ('351', 'AL', 'Alabama'),
    ('352', 'AL', 'Alabama'),
    ('354', 'AL', 'Alabama'),
    ('355', 'AL', 'Alabama'),
    ('356', 'AL', 'Alabama'),
    ('357', 'AL', 'Alabama'),
    ('358', 'AL', 'Alabama'),
    ('359', 'AL', 'Alabama'),
    ('360', 'AL', 'Alabama'),
    ('361', 'AL', 'Alabama'),
    ('362', 'AL', 'Alabama'),
    ('363', 'AL', 'Alabama'),
    ('364', 'AL', 'Alabama'),
    ('365', 'AL', 'Alabama'),
    ('366', 'AL', 'Alabama'),
    ('367', 'AL', 'Alabama'),
    ('368', 'AL', 'Alabama'),
    ('369', 'AL', 'Alabama'),
    ('370', 'TN', 'Tennessee'),
    ('371', 'TN', 'Tennessee'),
    ('372', 'TN', 'Tennessee'),
    ('373', 'TN', 'Tennessee'),
    ('374', 'TN', 'Tennessee'),
    ('375', 'TN', 'Tennessee'),
    ('376', 'TN', 'Tennessee'),
    ('377', 'TN', 'Tennessee'),
    ('378', 'TN', 'Tennessee'),
    ('379', 'TN', 'Tennessee'),
    ('380', 'TN', 'Tennessee'),
    ('381', 'TN', 'Tennessee'),
    ('382', 'TN', 'Tennessee'),
    ('383', 'TN', 'Tennessee'),
    ('384', 'TN', 'Tennessee'),
    ('385', 'TN', 'Tennessee'),
    ('386', 'MS', 'Mississippi'),
    ('387', 'MS', 'Mississippi'),
    ('388', 'MS', 'Mississippi'),
    ('389', 'MS', 'Mississippi'),
    ('390', 'MS', 'Mississippi'),
    ('391', 'MS', 'Mississippi'),
    ('392', 'MS', 'Mississippi'),
    ('393', 'MS', 'Mississippi'),
    ('394', 'MS', 'Mississippi'),
    ('395', 'MS', 'Mississippi'),
    ('396', 'MS', 'Mississippi'),
    ('397', 'MS', 'Mississippi'),
    ('398', 'GA', 'Georgia'),
    ('400', 'KY', 'Kentucky'),
    ('401', 'KY', 'Kentucky'),
    ('402', 'KY', 'Kentucky'),
    ('403', 'KY', 'Kentucky'),
    ('404', 'KY', 'Kentucky'),
    ('405', 'KY', 'Kentucky'),
    ('406', 'KY', 'Kentucky'),
    ('407', 'KY', 'Kentucky'),
    ('408', 'KY', 'Kentucky'),
    ('409', 'KY', 'Kentucky'),
    ('410', 'KY', 'Kentucky'),
    ('411', 'KY', 'Kentucky'),
    ('412', 'KY', 'Kentucky'),
    ('413', 'KY', 'Kentucky'),
    ('414', 'KY', 'Kentucky'),
    ('415', 'KY', 'Kentucky'),
    ('416', 'KY', 'Kentucky'),
    ('417', 'KY', 'Kentucky'),
    ('418', 'KY', 'Kentucky'),
    ('420', 'KY', 'Kentucky'),
    ('421', 'KY', 'Kentucky'),
    ('422', 'KY', 'Kentucky'),
    ('423', 'KY', 'Kentucky'),
    ('424', 'KY', 'Kentucky'),
    ('425', 'KY', 'Kentucky'),
    ('426', 'KY', 'Kentucky'),
    ('427', 'KY', 'Kentucky'),
    ('430', 'OH', 'Ohio'),
    ('431', 'OH', 'Ohio'),
    ('432', 'OH', 'Ohio'),
    ('433', 'OH', 'Ohio'),
    ('434', 'OH', 'Ohio'),
    ('435', 'OH', 'Ohio'),
    ('436', 'OH', 'Ohio'),
    ('437', 'OH', 'Ohio'),
    ('438', 'OH', 'Ohio'),
    ('439', 'OH', 'Ohio'),
    ('440', 'OH', 'Ohio'),
    ('441', 'OH', 'Ohio'),
    ('442', 'OH', 'Ohio'),
    ('443', 'OH', 'Ohio'),
    ('444', 'OH', 'Ohio'),
    ('445', 'OH', 'Ohio'),
    ('446', 'OH', 'Ohio'),
    ('447', 'OH', 'Ohio'),
    ('448', 'OH', 'Ohio'),
    ('449', 'OH', 'Ohio'),
    ('450', 'OH', 'Ohio'),
    ('451', 'OH', 'Ohio'),
    ('452', 'OH', 'Ohio'),
    ('453', 'OH', 'Ohio'),
    ('454', 'OH', 'Ohio'),
    ('455', 'OH', 'Ohio'),
    ('456', 'OH', 'Ohio'),
    ('457', 'OH', 'Ohio'),
    ('458', 'OH', 'Ohio'),
    ('460', 'IN', 'Indiana'),
    ('461', 'IN', 'Indiana'),
    ('462', 'IN', 'Indiana'),
    ('463', 'IN', 'Indiana'),
    ('464', 'IN', 'Indiana'),
    ('465', 'IN', 'Indiana'),
    ('466', 'IN', 'Indiana'),
    ('467', 'IN', 'Indiana'),
    ('468', 'IN', 'Indiana'),
    ('469', 'IN', 'Indiana'),
    ('470', 'IN', 'Indiana'),
    ('471', 'IN', 'Indiana'),
    ('472', 'IN', 'Indiana'),
    ('473', 'IN', 'Indiana'),
    ('474', 'IN', 'Indiana'),
    ('475', 'IN', 'Indiana'),
    ('476', 'IN', 'Indiana'),
    ('477', 'IN', 'Indiana'),
    ('478', 'IN', 'Indiana'),
    ('479', 'IN', 'Indiana'),
    ('480', 'MI', 'Michigan'),
    ('481', 'MI', 'Michigan'),
    ('482', 'MI', 'Michigan'),
    ('483', 'MI', 'Michigan'),
    ('484', 'MI', 'Michigan'),
    ('485', 'MI', 'Michigan'),
    ('486', 'MI', 'Michigan'),
    ('487', 'MI', 'Michigan'),
    ('488', 'MI', 'Michigan'),
    ('489', 'MI', 'Michigan'),
    ('490', 'MI', 'Michigan'),
    ('491', 'MI', 'Michigan'),
    ('492', 'MI', 'Michigan'),
    ('493', 'MI', 'Michigan'),
    ('494', 'MI', 'Michigan'),
    ('495', 'MI', 'Michigan'),
    ('496', 'MI', 'Michigan'),
    ('497', 'MI', 'Michigan'),
    ('498', 'MI', 'Michigan'),
    ('499', 'MI', 'Michigan'),
    ('500', 'IA', 'Iowa'),
    ('501', 'IA', 'Iowa'),
    ('502', 'IA', 'Iowa'),
    ('503', 'IA', 'Iowa'),
    ('504', 'IA', 'Iowa'),
    ('505', 'IA', 'Iowa'),
    ('506', 'IA', 'Iowa'),
    ('507', 'IA', 'Iowa'),
    ('508', 'IA', 'Iowa'),
    ('510', 'IA', 'Iowa'),
    ('511', 'IA', 'Iowa'),
    ('512', 'IA', 'Iowa'),
    ('513', 'IA', 'Iowa'),
    ('514', 'IA', 'Iowa'),
    ('515', 'IA', 'Iowa'),
    ('516', 'IA', 'Iowa'),
    ('520', 'IA', 'Iowa'),
    ('521', 'IA', 'Iowa'),
    ('522', 'IA', 'Iowa'),
    ('523', 'IA', 'Iowa'),
    ('524', 'IA', 'Iowa'),
    ('525', 'IA', 'Iowa'),
    ('526', 'IA', 'Iowa'),
    ('527', 'IA', 'Iowa'),
    ('528', 'IA', 'Iowa'),
    ('530', 'WI', 'Wisconsin'),
    ('531', 'WI', 'Wisconsin'),
    ('532', 'WI', 'Wisconsin'),
    ('534', 'WI', 'Wisconsin'),
    ('535', 'WI', 'Wisconsin'),
    ('537', 'WI', 'Wisconsin'),
    ('538', 'WI', 'Wisconsin'),
    ('539', 'WI', 'Wisconsin'),
    ('540', 'WI', 'Wisconsin'),
    ('541', 'WI', 'Wisconsin'),
    ('542', 'WI', 'Wisconsin'),
    ('543', 'WI', 'Wisconsin'),
    ('544', 'WI', 'Wisconsin'),
    ('545', 'WI', 'Wisconsin'),
    ('546', 'WI', 'Wisconsin'),
    ('547', 'WI', 'Wisconsin'),
    ('548', 'WI', 'Wisconsin'),
    ('549', 'WI', 'Wisconsin'),
    ('550', 'MN', 'Minnesota'),
    ('551', 'MN', 'Minnesota'),
    ('553', 'MN', 'Minnesota'),
    ('554', 'MN', 'Minnesota'),
    ('555', 'MN', 'Minnesota'),
    ('556', 'MN', 'Minnesota'),
    ('557', 'MN', 'Minnesota'),
    ('558', 'MN', 'Minnesota'),
    ('559', 'MN', 'Minnesota'),
    ('560', 'MN', 'Minnesota'),
    ('561', 'MN', 'Minnesota'),
    ('562', 'MN', 'Minnesota'),
    ('563', 'MN', 'Minnesota'),
    ('564', 'MN', 'Minnesota'),
    ('565', 'MN', 'Minnesota'),
    ('566', 'MN', 'Minnesota'),
    ('567', 'MN', 'Minnesota'),
    ('569', 'DC', 'District of Columbia'),
    ('570', 'SD', 'South Dakota'),
    ('571', 'SD', 'South Dakota'),
    ('572', 'SD', 'South Dakota'),
    ('573', 'SD', 'South Dakota'),
    ('574', 'SD', 'South Dakota'),
    ('575', 'SD', 'South Dakota'),
    ('576', 'SD', 'South Dakota'),
    ('577', 'SD', 'South Dakota'),
    ('580', 'ND', 'North Dakota'),
    ('581', 'ND', 'North Dakota'),
    ('582', 'ND', 'North Dakota'),
    ('583', 'ND', 'North Dakota'),
    ('584', 'ND', 'North Dakota'),
    ('585', 'ND', 'North Dakota'),
    ('586', 'ND', 'North Dakota'),
    ('587', 'ND', 'North Dakota'),
    ('588', 'ND', 'North Dakota'),
    ('590', 'MT', 'Montana'),
    ('591', 'MT', 'Montana'),
    ('592', 'MT', 'Montana'),
    ('593', 'MT', 'Montana'),
    ('594', 'MT', 'Montana'),
    ('595', 'MT', 'Montana'),
    ('596', 'MT', 'Montana'),
    ('597', 'MT', 'Montana'),
    ('598', 'MT', 'Montana'),
    ('599', 'MT', 'Montana'),
    ('600', 'IL', 'Illinois'),
    ('601', 'IL', 'Illinois'),
    ('602', 'IL', 'Illinois'),
    ('603', 'IL', 'Illinois'),
    ('604', 'IL', 'Illinois'),
    ('605', 'IL', 'Illinois'),
    ('606', 'IL', 'Illinois'),
    ('607', 'IL', 'Illinois'),
    ('608', 'IL', 'Illinois'),
    ('609', 'IL', 'Illinois'),
    ('610', 'IL', 'Illinois'),
    ('611', 'IL', 'Illinois'),
    ('612', 'IL', 'Illinois'),
    ('613', 'IL', 'Illinois'),
    ('614', 'IL', 'Illinois'),
    ('615', 'IL', 'Illinois'),
    ('616', 'IL', 'Illinois'),
    ('617', 'IL', 'Illinois'),
    ('618', 'IL', 'Illinois'),
    ('619', 'IL', 'Illinois'),
    ('620', 'IL', 'Illinois'),
    ('622', 'IL', 'Illinois'),
    ('623', 'IL', 'Illinois'),
    ('624', 'IL', 'Illinois'),
    ('625', 'IL', 'Illinois'),
    ('626', 'IL', 'Illinois'),
    ('627', 'IL', 'Illinois'),
    ('628', 'IL', 'Illinois'),
    ('629', 'IL', 'Illinois'),
    ('630', 'MO', 'Missouri'),
    ('631', 'MO', 'Missouri'),
    ('633', 'MO', 'Missouri'),
    ('634', 'MO', 'Missouri'),
    ('635', 'MO', 'Missouri'),
    ('636', 'MO', 'Missouri'),
    ('637', 'MO', 'Missouri'),
    ('638', 'MO', 'Missouri'),
    ('639', 'MO', 'Missouri'),
    ('640', 'MO', 'Missouri'),
    ('641', 'MO', 'Missouri'),
    ('644', 'MO', 'Missouri'),
    ('645', 'MO', 'Missouri'),
    ('646', 'MO', 'Missouri'),
    ('647', 'MO', 'Missouri'),
    ('648', 'MO', 'Missouri'),
    ('650', 'MO', 'Missouri'),
    ('651', 'MO', 'Missouri'),
    ('652', 'MO', 'Missouri'),
    ('653', 'MO', 'Missouri'),
    ('654', 'MO', 'Missouri'),
    ('655', 'MO', 'Missouri'),
    ('656', 'MO', 'Missouri'),
    ('657', 'MO', 'Missouri'),
    ('658', 'MO', 'Missouri'),
    ('660', 'KS', 'Kansas'),
    ('661', 'KS', 'Kansas'),
    ('662', 'KS', 'Kansas'),
    ('664', 'KS', 'Kansas'),
    ('665', 'KS', 'Kansas'),
    ('666', 'KS', 'Kansas'),
    ('667', 'KS', 'Kansas'),
    ('668', 'KS', 'Kansas'),
    ('669', 'KS', 'Kansas'),
    ('670', 'KS', 'Kansas'),
    ('671', 'KS', 'Kansas'),
    ('672', 'KS', 'Kansas'),
    ('673', 'KS', 'Kansas'),
    ('674', 'KS', 'Kansas'),
    ('675', 'KS', 'Kansas'),
    ('676', 'KS', 'Kansas'),
    ('677', 'KS', 'Kansas'),
    ('678', 'KS', 'Kansas'),
    ('679', 'KS', 'Kansas'),
    ('680', 'NE', 'Nebraska'),
    ('681', 'NE', 'Nebraska'),
    ('683', 'NE', 'Nebraska'),
    ('684', 'NE', 'Nebraska'),
    ('685', 'NE', 'Nebraska'),
    ('686', 'NE', 'Nebraska'),
    ('687', 'NE', 'Nebraska'),
    ('688', 'NE', 'Nebraska'),
    ('689', 'NE', 'Nebraska'),
    ('690', 'NE', 'Nebraska'),
    ('691', 'NE', 'Nebraska'),
    ('692', 'NE', 'Nebraska'),
    ('693', 'NE', 'Nebraska'),
    ('700', 'LA', 'Louisiana'),
    ('701', 'LA', 'Louisiana'),
    ('703', 'LA', 'Louisiana'),
    ('704', 'LA', 'Louisiana'),
    ('705', 'LA', 'Louisiana'),
    ('706', 'LA', 'Louisiana'),
    ('707', 'LA', 'Louisiana'),
    ('708', 'LA', 'Louisiana'),
    ('710', 'LA', 'Louisiana'),
    ('711', 'LA', 'Louisiana'),
    ('712', 'LA', 'Louisiana'),
    ('713', 'LA', 'Louisiana'),
    ('714', 'LA', 'Louisiana'),
    ('716', 'AR', 'Arkansas'),
    ('717', 'AR', 'Arkansas'),
    ('718', 'AR', 'Arkansas'),
    ('719', 'AR', 'Arkansas'),
    ('720', 'AR', 'Arkansas'),
    ('721', 'AR', 'Arkansas'),
    ('722', 'AR', 'Arkansas'),
    ('723', 'AR', 'Arkansas'),
    ('724', 'AR', 'Arkansas'),
    ('725', 'AR', 'Arkansas'),
    ('726', 'AR', 'Arkansas'),
    ('727', 'AR', 'Arkansas'),
    ('728', 'AR', 'Arkansas'),
    ('729', 'AR', 'Arkansas'),
    ('730', 'OK', 'Oklahoma'),
    ('731', 'OK', 'Oklahoma'),
    ('733', 'TX', 'Texas'),
    ('734', 'OK', 'Oklahoma'),
    ('735', 'OK', 'Oklahoma'),
    ('736', 'OK', 'Oklahoma'),
    ('737', 'OK', 'Oklahoma'),
    ('738', 'OK', 'Oklahoma'),
    ('739', 'OK', 'Oklahoma'),
    ('740', 'OK', 'Oklahoma'),
    ('741', 'OK', 'Oklahoma'),
    ('743', 'OK', 'Oklahoma'),
    ('744', 'OK', 'Oklahoma'),
    ('745', 'OK', 'Oklahoma'),
    ('746', 'OK', 'Oklahoma'),
    ('747', 'OK', 'Oklahoma'),
    ('748', 'OK', 'Oklahoma'),
    ('749', 'OK', 'Oklahoma'),
    ('750', 'TX', 'Texas'),
    ('751', 'TX', 'Texas'),
    ('752', 'TX', 'Texas'),
    ('753', 'TX', 'Texas'),
    ('754', 'TX', 'Texas'),
    ('755', 'TX', 'Texas'),
    ('756', 'TX', 'Texas'),
    ('757', 'TX', 'Texas'),
    ('758', 'TX', 'Texas'),
    ('759', 'TX', 'Texas'),
    ('760', 'TX', 'Texas'),
    ('761', 'TX', 'Texas'),
    ('762', 'TX', 'Texas'),
    ('763', 'TX', 'Texas'),
    ('764', 'TX', 'Texas'),
    ('765', 'TX', 'Texas'),
    ('766', 'TX', 'Texas'),
    ('767', 'TX', 'Texas'),
    ('768', 'TX', 'Texas'),
    ('769', 'TX', 'Texas'),
    ('770', 'TX', 'Texas'),
    ('771', 'TX', 'Texas'),
    ('772', 'TX', 'Texas'),
    ('773', 'TX', 'Texas'),
    ('774', 'TX', 'Texas'),
    ('775', 'TX', 'Texas'),
    ('776', 'TX', 'Texas'),
    ('777', 'TX', 'Texas'),
    ('778', 'TX', 'Texas'),
    ('779', 'TX', 'Texas'),
    ('780', 'TX', 'Texas'),
    ('781', 'TX', 'Texas'),
    ('782', 'TX', 'Texas'),
    ('783', 'TX', 'Texas'),
    ('784', 'TX', 'Texas'),
    ('785', 'TX', 'Texas'),
    ('786', 'TX', 'Texas'),
    ('787', 'TX', 'Texas'),
    ('788', 'TX', 'Texas'),
    ('789', 'TX', 'Texas'),
    ('790', 'TX', 'Texas'),
    ('791', 'TX', 'Texas'),
    ('792', 'TX', 'Texas'),
    ('793', 'TX', 'Texas'),
    ('794', 'TX', 'Texas'),
    ('795', 'TX', 'Texas'),
    ('796', 'TX', 'Texas'),
    ('797', 'TX', 'Texas'),
    ('798', 'TX', 'Texas'),
    ('799', 'TX', 'Texas'),
    ('800', 'CO', 'Colorado'),
    ('801', 'CO', 'Colorado'),
    ('802', 'CO', 'Colorado'),
    ('803', 'CO', 'Colorado'),
    ('804', 'CO', 'Colorado'),
    ('805', 'CO', 'Colorado'),
    ('806', 'CO', 'Colorado'),
    ('807', 'CO', 'Colorado'),
    ('808', 'CO', 'Colorado'),
    ('809', 'CO', 'Colorado'),
    ('810', 'CO', 'Colorado'),
    ('811', 'CO', 'Colorado'),
    ('812', 'CO', 'Colorado'),
    ('813', 'CO', 'Colorado'),
    ('814', 'CO', 'Colorado'),
    ('815', 'CO', 'Colorado'),
    ('816', 'CO', 'Colorado'),
    ('820', 'WY', 'Wyoming'),
    ('821', 'WY', 'Wyoming'),
    ('822', 'WY', 'Wyoming'),
    ('823', 'WY', 'Wyoming'),
    ('824', 'WY', 'Wyoming'),
    ('825', 'WY', 'Wyoming'),
    ('826', 'WY', 'Wyoming'),
    ('827', 'WY', 'Wyoming'),
    ('828', 'WY', 'Wyoming'),
    ('829', 'WY', 'Wyoming'),
    ('830', 'WY', 'Wyoming'),
    ('831', 'WY', 'Wyoming'),
    ('832', 'ID', 'Idaho'),
    ('833', 'ID', 'Idaho'),
    ('834', 'ID', 'Idaho'),
    ('835', 'ID', 'Idaho'),
    ('836', 'ID', 'Idaho'),
    ('837', 'ID', 'Idaho'),
    ('838', 'ID', 'Idaho'),
    ('840', 'UT', 'Utah'),
    ('841', 'UT', 'Utah'),
    ('843', 'UT', 'Utah'),
    ('844', 'UT', 'Utah'),
    ('845', 'UT', 'Utah'),
    ('846', 'UT', 'Utah'),
    ('847', 'UT', 'Utah'),
    ('850', 'AZ', 'Arizona'),
    ('851', 'AZ', 'Arizona'),
    ('852', 'AZ', 'Arizona'),
    ('853', 'AZ', 'Arizona'),
    ('855', 'AZ', 'Arizona'),
    ('856', 'AZ', 'Arizona'),
    ('857', 'AZ', 'Arizona'),
    ('859', 'AZ', 'Arizona'),
    ('860', 'AZ', 'Arizona'),
    ('863', 'AZ', 'Arizona'),
    ('864', 'AZ', 'Arizona'),
    ('865', 'AZ', 'Arizona'),
    ('870', 'NM', 'New Mexico'),
    ('871', 'NM', 'New Mexico'),
    ('873', 'NM', 'New Mexico'),
    ('874', 'NM', 'New Mexico'),
    ('875', 'NM', 'New Mexico'),
    ('877', 'NM', 'New Mexico'),
    ('878', 'NM', 'New Mexico'),
    ('879', 'NM', 'New Mexico'),
    ('880', 'NM', 'New Mexico'),
    ('881', 'NM', 'New Mexico'),
    ('882', 'NM', 'New Mexico'),
    ('883', 'NM', 'New Mexico'),
    ('884', 'NM', 'New Mexico'),
    ('885', 'NM', 'New Mexico'),
    ('890', 'NV', 'Nevada'),
    ('891', 'NV', 'Nevada'),
    ('893', 'NV', 'Nevada'),
    ('894', 'NV', 'Nevada'),
    ('895', 'NV', 'Nevada'),
    ('897', 'NV', 'Nevada'),
    ('898', 'NV', 'Nevada'),
    ('900', 'CA', 'California'),
    ('901', 'CA', 'California'),
    ('902', 'CA', 'California'),
    ('903', 'CA', 'California'),
    ('904', 'CA', 'California'),
    ('905', 'CA', 'California'),
    ('906', 'CA', 'California'),
    ('907', 'CA', 'California'),
    ('908', 'CA', 'California'),
    ('910', 'CA', 'California'),
    ('911', 'CA', 'California'),
    ('912', 'CA', 'California'),
    ('913', 'CA', 'California'),
    ('914', 'CA', 'California'),
    ('915', 'CA', 'California'),
    ('916', 'CA', 'California'),
    ('917', 'CA', 'California'),
    ('918', 'CA', 'California'),
    ('919', 'CA', 'California'),
    ('920', 'CA', 'California'),
    ('921', 'CA', 'California'),
    ('922', 'CA', 'California'),
    ('923', 'CA', 'California'),
    ('924', 'CA', 'California'),
    ('925', 'CA', 'California'),
    ('926', 'CA', 'California'),
    ('927', 'CA', 'California'),
    ('928', 'CA', 'California'),
    ('930', 'CA', 'California'),
    ('931', 'CA', 'California'),
    ('932', 'CA', 'California'),
    ('933', 'CA', 'California'),
    ('934', 'CA', 'California'),
    ('935', 'CA', 'California'),
    ('936', 'CA', 'California'),
    ('937', 'CA', 'California'),
    ('938', 'CA', 'California'),
    ('939', 'CA', 'California'),
    ('940', 'CA', 'California'),
    ('941', 'CA', 'California'),
    ('942', 'CA', 'California'),
    ('943', 'CA', 'California'),
    ('944', 'CA', 'California'),
    ('945', 'CA', 'California'),
    ('946', 'CA', 'California'),
    ('947', 'CA', 'California'),
    ('948', 'CA', 'California'),
    ('949', 'CA', 'California'),
    ('950', 'CA', 'California'),
    ('951', 'CA', 'California'),
    ('952', 'CA', 'California'),
    ('953', 'CA', 'California'),
    ('954', 'CA', 'California'),
    ('955', 'CA', 'California'),
    ('956', 'CA', 'California'),
    ('957', 'CA', 'California'),
    ('958', 'CA', 'California'),
    ('959', 'CA', 'California'),
    ('960', 'CA', 'California'),
    ('961', 'CA', 'California'),
    ('967', 'HI', 'Hawaii'),
    ('968', 'HI', 'Hawaii'),
    ('970', 'OR', 'Oregon'),
    ('971', 'OR', 'Oregon'),
    ('972', 'OR', 'Oregon'),
    ('973', 'OR', 'Oregon'),
    ('974', 'OR', 'Oregon'),
    ('975', 'OR', 'Oregon'),
    ('976', 'OR', 'Oregon'),
    ('977', 'OR', 'Oregon'),
    ('978', 'OR', 'Oregon'),
    ('979', 'OR', 'Oregon'),
    ('980', 'WA', 'Washington'),
    ('981', 'WA', 'Washington'),
    ('982', 'WA', 'Washington'),
    ('983', 'WA', 'Washington'),
    ('984', 'WA', 'Washington'),
    ('985', 'WA', 'Washington'),
    ('986', 'WA', 'Washington'),
    ('988', 'WA', 'Washington'),
    ('989', 'WA', 'Washington'),
    ('990', 'WA', 'Washington'),
    ('991', 'WA', 'Washington'),
    ('992', 'WA', 'Washington'),
    ('993', 'WA', 'Washington'),
    ('994', 'WA', 'Washington'),
    ('995', 'AK', 'Alaska'),
    ('996', 'AK', 'Alaska'),
    ('997', 'AK', 'Alaska'),
    ('998', 'AK', 'Alaska'),
    ('999', 'AK', 'Alaska'))


class Country(Enum):
    """Countries."""

    anguilla = Constant('Anguilla', '995f66a0-5d95-e211-a939-e4115bead28a')
    argentina = Constant('Argentina', '9c5f66a0-5d95-e211-a939-e4115bead28a')
    azerbaijan = Constant('Azerbaijan', 'a15f66a0-5d95-e211-a939-e4115bead28a')
    canada = Constant('Canada', '5daf72a6-5d95-e211-a939-e4115bead28a')
    cayman_islands = Constant('Cayman Islands', '5faf72a6-5d95-e211-a939-e4115bead28a')
    france = Constant('France', '82756b9a-5d95-e211-a939-e4115bead28a')
    greece = Constant('Greece', 'e3f682ac-5d95-e211-a939-e4115bead28a')
    ireland = Constant('Ireland', '736a9ab2-5d95-e211-a939-e4115bead28a')
    isle_of_man = Constant('Isle of Man', '79756b9a-5d95-e211-a939-e4115bead28a')
    italy = Constant('Italy', '84756b9a-5d95-e211-a939-e4115bead28a')
    japan = Constant('Japan', '85756b9a-5d95-e211-a939-e4115bead28a')
    montserrat = Constant('Montserrat', '1350bdb8-5d95-e211-a939-e4115bead28a')
    united_kingdom = Constant('United Kingdom', '80756b9a-5d95-e211-a939-e4115bead28a')
    united_states = CountryConstant(
        'United States',
        '81756b9a-5d95-e211-a939-e4115bead28a',
        (r'^.*?(?:(\d{5}-\d{4})|(\d{5}\s-\s\d{4})'
         r'|(\d{5}\s–\s\d{4})|(\d{9})|(\d)\s?(\d{4})).*?$'),
        r'\1\2\3\4\5\6',
    )


class SectorCluster(Enum):
    """Sector clusters."""

    creative_lifestyle_and_learning = Constant(
        'Creative, Lifestyle and Learning',
        'ed3671b5-d194-4ee3-9bbf-a04773711dd9',
    )
    defence_and_security = Constant(
        'Defence and Security',
        '7cdae131-6fc4-4c4c-a977-07f5be64a1c4',
    )
    energy_and_infrastructure = Constant(
        'Energy & Infrastructure',
        'c79ec2c9-9b31-45a0-9d32-b5cc284dc8d1',
    )
    financial_and_professional_services = Constant(
        'Financial & Professional Services',
        '7be7a38f-1a77-44bf-abee-3049ba50a6a8',
    )
    healthcare_life_sciences_and_bio_economy = Constant(
        'Healthcare, Life Sciences and Bio-Economy',
        '0804745e-80b6-4bd1-8101-30e7a431623e',
    )
    technology_entrepreneurship_and_advanced_manufacturing = Constant(
        'Technology, Entrepreneurship and Advanced Manufacturing',
        '531d3510-3f42-41fd-86b5-fa686fdfe33f',
    )


class Sector(Enum):
    """Sectors (not all of them!)."""

    aerospace_assembly_aircraft = Constant(
        'Aerospace : Manufacturing and Assembly : Aircraft',
        'b422c9d2-5f95-e211-a939-e4115bead28a',
    )
    renewable_energy_wind = Constant(
        'Renewable Energy : Wind',
        'a4959812-6095-e211-a939-e4115bead28a',
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
        'Yorkshire and The Humber', '834cd12a-6095-e211-a939-e4115bead28a',
    )


class Service(Enum):
    """Service."""

    enquiry_or_referral_received = Constant(
        'Enquiry or Referral Received',
        'fee6779d-e127-4e1e-89f6-d614b4df3581',
    )

    inbound_referral = Constant(
        'Enquiry or Referral Received : Other Inbound Export Referral',
        '9984b82b-3499-e211-a939-e4115bead28a',
    )
    account_management = Constant(
        'Account Management : General',
        '9484b82b-3499-e211-a939-e4115bead28a',
    )

    providing_investment_advice_and_information = Constant(
        'Providing Investment Advice & Information',
        'ef3218c1-bed6-4ad8-b8d5-8af2430d32ff',
    )
    making_export_introductions = Constant(
        'Making Export Introductions',
        '1477622e-9adb-4017-8d8d-fe3221f1d2fc',
    )

    investment_enquiry_requested_more_information = Constant(
        'Investment Enquiry – Requested more information from source (IST use only)',
        '73ceedc1-c139-4bdf-9e47-17b1bae488da',
    )
    investment_enquiry_confirmed_prospect = Constant(
        'Investment Enquiry – Confirmed prospect project status (IST use only)',
        '4f142041-2b9d-4776-ace8-22612260eae6',
    )
    investment_enquiry_assigned_to_ist_sas = Constant(
        'Investment Enquiry – Assigned to IST-SAS (IST use only)',
        'c579b89b-d49d-4926-a6a4-0a1459cd25cb',
    )
    investment_enquiry_assigned_to_ist_cmc = Constant(
        'Investment Enquiry – Assigned to IST-CMC (IST use only)',
        '2591b204-8a31-4824-a93b-d7a03dca8cb5',
    )
    investment_enquiry_assigned_to_hq = Constant(
        'Investment Enquiry – Assigned to HQ (IST use only)',
        '38a67092-f485-4ea1-8a1a-402b949d2d13',
    )
    investment_enquiry_transferred_to_lep = Constant(
        'Investment Enquiry – Transferred to LEP (IST use only)',
        '48e6bc3e-56c5-4bdc-a718-093614547d73',
    )
    investment_enquiry_transferred_to_da = Constant(
        'Investment Enquiry – Transferred to DA (IST use only)',
        '05c8175a-abf5-4cc6-af34-bcee8699fd4b',
    )
    investment_enquiry_transferred_to_lp = Constant(
        'Investment Enquiry – Transferred to L&P (IST use only)',
        'c707f81d-ae66-490a-98f5-575438944c43',
    )
    investment_ist_aftercare_offered = Constant(
        'Investment - IST Aftercare Offered (IST use only)',
        '79824229-fd87-483f-b929-8f2b9531492b',
    )


class Team(Enum):
    """Team."""

    healthcare_uk = Constant('Healthcare UK', '3ff47a07-002c-e311-a78e-e4115bead28a')
    tees_valley_lep = Constant('Tees Valley LEP', 'a889ef76-8925-e511-b6bc-e4115bead28a')
    td_events_healthcare = Constant(
        'TD - Events - Healthcare', 'daf924aa-9698-e211-a939-e4115bead28a',
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
        'Prospect', '8a320cc9-ae2e-443e-9d26-2f36452c2ced', 200.0,
    )
    assign_pm = OrderedConstant(
        'Assign PM', 'c9864359-fb1a-4646-a4c1-97d10189fc03', 300.0,
    )
    active = OrderedConstant(
        'Active', '7606cc19-20da-4b74-aba1-2cec0d753ad8', 400.0,
    )
    verify_win = OrderedConstant(
        'Verify win', '49b8f6f3-0c50-4150-a965-2c974f3149e3', 500.0,
    )
    won = OrderedConstant('Won', '945ea6d1-eee3-4f5b-9144-84a75b71b8e6', 600.0)

    @classmethod
    def get_by_id(cls, item_id):
        """Gets the corresponding item for a given id."""
        return next(
            (item for item in cls if str(item.value.id) == str(item_id)),
            None,
        )


class InvestmentType(Enum):
    """Investment type constants."""

    fdi = Constant('FDI', '3e143372-496c-4d1e-8278-6fdd3da9b48b')
    non_fdi = Constant('Non-FDI', '9c364e64-2b28-401b-b2df-50e08b0bca44')
    commitment_to_invest = Constant(
        'Commitment to invest',
        '031269ab-b7ec-40e9-8a4e-7371404f0622',
    )


class ReferralSourceActivity(Enum):
    """Referral source activity constants."""

    cold_call = Constant(
        'Cold call', '0c4f8e74-d34f-4aca-b764-a44cdc2d0087',
    )
    direct_enquiry = Constant(
        'Direct enquiry', '7d98f3a6-3e3f-40ac-a6f3-3f0c251ec1d2',
    )
    event = Constant(
        'Event', '3816a95b-6a76-4ad0-8ae9-b0d7e7d2b79c',
    )
    marketing = Constant(
        'Marketing', '0acf0e68-e09e-4e5d-92b6-e72e5a5c7ea4',
    )
    multiplier = Constant(
        'Multiplier', 'e95cddb3-9407-4c8a-b5a6-2616117b0aae',
    )
    none = Constant(
        'None', 'aba8f653-264f-48d8-950e-07f9c418c7b0',
    )
    other = Constant(
        'Other', '318e6e9e-2a0e-4e4b-a495-c48aeee4b996',
    )
    relationship_management_activity = Constant(
        'Relationship management activity',
        '668e999c-a669-4d9b-bfbf-6275ceed86da',
    )
    personal_reference = Constant(
        'Personal reference', 'c03c4043-18b4-4463-a36b-a1af1b35f95d',
    )
    website = Constant(
        'Website', '812b2f62-fe62-4cc8-b69c-58f3e2ebac17',
    )


class InvestmentBusinessActivity(Enum):
    """Investment business activity constants."""

    sales = Constant('Sales', '71946309-c92c-4c5b-9c42-8502cc74c72e')
    retail = Constant('Retail', 'a2dbd807-ae52-421c-8d1d-88adfc7a506b')
    other = Constant('Other', 'befab707-5abd-4f47-8477-57f091e6dac9')


class FDIType(Enum):
    """Investment FDI type constants."""

    creation_of_new_site_or_activity = Constant(
        'Creation of new site or activity',
        'f8447013-cfdc-4f35-a146-6619665388b3',
    )


class FDIValue(Enum):
    """Investment FDI value constants."""

    higher = Constant(
        'Higher', '38e36c77-61ad-4186-a7a8-ac6a1a1104c6',
    )


class SalaryRange(Enum):
    """Average salary constants."""

    below_25000 = OrderedConstant(
        'Below £25,000', '2943bf3d-32dd-43be-8ad4-969b006dee7b', 100.0,
    )


class InvestmentStrategicDriver(Enum):
    """Investment strategic driver constants."""

    access_to_market = Constant(
        'Access to market', '382aa6d1-a362-4166-a09d-f579d9f3be75',
    )


class ExportSegment(Enum):
    """ExportSegment type constants."""

    hep = Constant('hep', 'High export potential')
    non_hep = Constant('non-hep', 'Not high export potential')


class ExportSubSegment(Enum):
    """ExportSubSegment type constants."""

    sustain_nurture_and_grow = Constant(
        'sustain_nurture_and_grow',
        'Sustain: nurture & grow',
    )
    sustain_develop_export_capability = Constant(
        'sustain_develop_export_capability',
        'Sustain: develop export capability',
    )
    sustain_communicate_benefits = Constant(
        'sustain_communicate_benefits',
        'Sustain: communicate benefits',
    )
    sustain_increase_competitiveness = Constant(
        'sustain_increase_competitiveness',
        'Sustain: increase competitiveness',
    )
    reassure_nurture_and_grow = Constant(
        'reassure_nurture_and_grow',
        'Reassure: nurture & grow',
    )
    reassure_develop_export_capability = Constant(
        'reassure_develop_export_capability',
        'Reassure: develop export capability',
    )
    reassure_leave_be = Constant(
        'reassure_leave_be',
        'Reassure: leave be',
    )
    reassure_change_the_game = Constant(
        'reassure_change_the_game',
        'Reassure: change the game',
    )
    promote_develop_export_capability = Constant(
        'promote_develop_export_capability',
        'Promote: develop export capability',
    )
    promote_communicate_benefits = Constant(
        'promote_communicate_benefits',
        'Promote: communicate benefits',
    )
    promote_change_the_game = Constant(
        'promote_change_the_game',
        'Promote: change the game',
    )
    challenge = Constant('challenge', 'Challenge')

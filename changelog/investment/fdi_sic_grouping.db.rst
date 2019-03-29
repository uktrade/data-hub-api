The database table ``investment_fdisicgrouping`` has been added with the following columns:

- id (uuid) not null,
- name (text) not null,
- disabled_on (datetime),


The database table ``investment_gva_multiplier`` has been added with the following columns:

- id (uuid) not null,
- multiplier (float) not null,
- financial_year (int) not null,
- fdisicgrouping_id (uuid) not null,

Where ``fdi_sicgrouping_id`` is a foreign key to ``investment_fdisicgrouping``.


The database table ``investment_investmentsector`` has been added with the following columns:

- sector_id (uuid) not null pk,
- fdi_sicgrouping_id (uuid) not null,

Where ``sector_id`` is a foreign key to ``metadata_sector`` and
``fdi_sicgrouping_id`` is a foreign key to ``investment_fdisicgrouping``.



The database_table ``investment_investmentproject`` has been updated and the following column has been added:

- gva_multiplier_id (uuid),

Where ``gva_multiplier_id`` is a foreign key to ``investment_gvamultiplier``.

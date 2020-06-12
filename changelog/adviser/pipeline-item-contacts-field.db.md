The table ``company_list_pipelineitem_contacts`` with columns ``("id" serial NOT NULL PRIMARY KEY, "pipelineitem_id" uuid NOT NULL, "contact_id" uuid NOT NULL)`` was added. This is a many-to-many table linking pipeline item with contacts, that will eventually replace ``company_list_pipelineitem.contact_id`` field.

The table had not been fully populated with data yet; continue to use ``company_list_pipelineitem.contact_id`` for the time being.

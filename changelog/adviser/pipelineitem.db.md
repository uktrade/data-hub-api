A `company_list_pipelineitem` table was created with the following columns:

      - `"id" uuid NOT NULL PRIMARY KEY`
      - `"adviser_id" uuid NOT NULL`
      - `"company_id" uuid NOT NULL`
      - `"status" character varying(255) NOT NULL`
      - `"created_on" timestamp with time zone NULL`
      - `"modified_on" timestamp with time zone NULL`
      - `"created_by_id" uuid NULL`
      - `"modified_by_id" uuid NULL`
    
    This table will store a list of companies advisers have added to their personal pipeline with a predefined status of Leads or In progress or Win.
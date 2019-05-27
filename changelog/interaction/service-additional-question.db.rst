The database table ``interaction_serviceadditionalquestion`` has been added with the following columns:

- ``id uuid not null``

- ``disabled_on timestamp with time zone``

- ``name text not null``

- ``is_required boolean not null``

- ``type character varying(255) not null``

- ``order double precision not null``

- ``answer_option_id uuid not null``

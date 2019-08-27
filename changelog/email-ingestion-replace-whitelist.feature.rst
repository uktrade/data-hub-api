The email ingestion whitelist was removed so that email ingestion is open to
all DIT advisers.  
The email domain that a DIT adviser uses to send an email to Data Hub must be 
known to Data Hub through a ``DIT_EMAIL_DOMAIN_<domain>`` django setting -
there is no longer a default domain authentication value. This ensures that 
email ingestion is locked down to domains that we know the authentication
signature for.

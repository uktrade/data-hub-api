Email ingestion was adjusted so that emails are deleted after they are ingested.
Previously, email ingestion would mark the emails as "seen" but now that we are
out of the pilot for meeting invite ingestion we have switched to deletes as this
is safer for data retention/protection reasons.

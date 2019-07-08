A new ``notification`` django app was added for the purpose of sending notifications
to Data Hub advisers and contacts.  This is a wrapper around the GOVUK Notify 
service and will be used initially for sending receipt/bounce notifications to 
advisers who use the meeting invite email ingestion tool.

The app has not yet been added to ``settings.INSTALLED_APPS``; this will happen
as part of the follow-up work to use the notification app in the meeting invite
email ingestion logic.

Activated a feature for ingesting meeting invite emails sent to a shared mailbox as draft
interactions. This enables DIT advisers to create interactions more easily.

This is the first instance of a Data Hub app using the framework provided by the
``datahub.email_ingestion`` app.  There will be subsequent iterations on the 
``CalendarInteractionEmailProcessor`` class to improve the user experience - most
notably sending notifications of bounce/receipt to advisers.

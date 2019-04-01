It's now possible for advisers to send meeting requests to a monitored 
"meetings" inbox and have Data Hub ingest these meeting requests as interactions.

Data Hub now has the ability to monitor email inboxes - via IMAP - and process
new messages according to business logic provided by ``EmailProcessor`` classes.
Meeting invites are emails which follow a certain established signature - the
``CalendarInteractionEmailProcessor`` class parses emails and extracts the 
necessary data to create an incomplete Interaction which represents the meeting.

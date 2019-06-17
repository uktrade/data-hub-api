A mechanism was added to suppress email ingestion IMAP connection errors until
a configurable threshold is met within a window of 10 tries. This helps reduce
noise in error reporting occurring from occasional connection errors to flaky
external IMAP endpoints.

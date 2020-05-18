For existing endpoint `/v4/pipeline-item`, extend the logic to restrict fields per status on the `POST` method. After this change, if any field below for the given status is present in the request body, a `400` will be thrown.

- Fields: likelihood_to_win, potential_value, expected_win_date / Status: WIN
- Fields: likelihood_to_win, potential_value, expected_win_date, sector / Status: LEADS

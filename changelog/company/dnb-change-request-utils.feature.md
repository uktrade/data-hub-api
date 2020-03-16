Utility functions were added to the Data Hub API for sending change-requests to dnb-service and returning the response back to the clients.

The `request_change` utility function was hooked up to the `DNBCompanyChangeRequestView` and tests were added to ensure we are keeping to the agreed contract with the client as well as `dnb-service`.

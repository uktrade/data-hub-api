Companies now define fields for a mandatory address representing the main location for the business and fields for an optional registered address.
Trading address fields are still automatically updated but deprecated.
The data was migrated in the following way:

- address fields: populated from trading address or (as fallback) registered address in this specific order.
- registered fields: kept untouched for now but will be overridden by the values from Companies House where possible or (as fallback) set to blank values. A deprecation notice will be announced before this happens.

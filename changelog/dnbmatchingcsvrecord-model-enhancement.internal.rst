The following fields were added to ``dnbmatchingcsvrecord`` to support selection of match candidates:

* ``selected_duns_number`` - (char, nullable) - holds currently selected duns_number of the company from match candidates
* ``selected_by`` - (adviser, nullable) - adviser who made a selection or provided explanation for no selection
* ``selected_on`` - (datetime, nullable) - when selection has been made
* ``no_match_reason`` - (char, nullable) - why selection could not be made
* ``no_match_description`` - (text, nullable) - more information about why selection could not be made

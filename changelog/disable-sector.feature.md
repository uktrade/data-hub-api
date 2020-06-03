A `disable_sector` management command was added for disabling sectors that are no longer used.

This will be initially run as part of a large sector migration exercise involving the renaming, moving and splitting of sector segments. As a result of this migration many sectors will no longer be required and should therefore be disabled.
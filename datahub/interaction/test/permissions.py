from datahub.interaction.models import InteractionPermission


NON_RESTRICTED_VIEW_PERMISSIONS = (
    (
        InteractionPermission.view_all,
    ),
    (
        InteractionPermission.view_all,
        InteractionPermission.view_associated_investmentproject,
    ),
)


NON_RESTRICTED_ADD_PERMISSIONS = (
    (
        InteractionPermission.add_all,
    ),
    (
        InteractionPermission.add_all,
        InteractionPermission.add_associated_investmentproject,
    ),
)


NON_RESTRICTED_CHANGE_PERMISSIONS = (
    (
        InteractionPermission.change_all,
    ),
    (
        InteractionPermission.change_all,
        InteractionPermission.change_associated_investmentproject,
    ),
)

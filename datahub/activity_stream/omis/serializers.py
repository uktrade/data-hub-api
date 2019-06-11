from datahub.activity_stream.serializers import ActivitySerializer


class OMISOrderAddedSerializer(ActivitySerializer):
    """
    OMIS Order added serializer for activity stream.
    """

    def to_representation(self, instance):
        """
        Serialize the OMIS order as per activity stream spec:
        https://www.w3.org/TR/activitystreams-core/
        """
        order_id = f'dit:DataHubOMISOrder:{instance.pk}'
        order = {
            'id': f'{order_id}:Add',
            'type': 'Add',
            'published': instance.created_on,
            'generator': self._get_generator(),
            'object': {
                'id': order_id,
                'type': [f'dit:OMISOrder'],
                'name': instance.reference,
                'attributedTo': [
                    self._get_company(instance.company),
                    self._get_contact(instance.contact),
                ],
                'url': instance.get_absolute_url(),
            },
        }

        if instance.created_by is not None:
            order['actor'] = self._get_adviser(instance.created_by)

        if instance.primary_market is not None:
            order['object']['dit:country'] = {
                'name': instance.primary_market.name,
            }

        if instance.uk_region is not None:
            order['object']['dit:ukRegion'] = {
                'name': instance.uk_region.name,
            }

        return order

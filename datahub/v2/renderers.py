from rest_framework import renderers


class JSONRenderer(renderers.JSONRenderer):
    """Take data and convert them in the right format.

    Output format:
    {
            "data": {
                "type": "identities",
                "id": 1,
                "attributes": {
                    "first_name": "John",
                    "last_name": "Coltrane"
                }
            }
        }

    """

    media_type = 'application/vnd.api+json'
    format = 'vnd.api+json'

    def render_errors(self, data, accepted_media_type=None, renderer_context=None):
        """Handle the errors rendering."""
        return super(JSONRenderer, self).render(
            data, accepted_media_type, renderer_context
        )

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Produce the json to be rendered.

        data is a RepoResponse class instance.
        """
        renderer_context = renderer_context or {}
        view = renderer_context.get('view')
        response = renderer_context.get('response')
        if view_has_errors(view):
            data = {'errors': format_errors(data)}
            return self.render_errors(data, accepted_media_type, renderer_context)

        render_data = {'data': data.data}
        if isinstance(data.data, list):
            render_data['meta'] = data.metadata
            render_data['links'] = data.links
        if data.status:  # 201
            response.status_code = data.status
        return super(JSONRenderer, self).render(
            render_data, accepted_media_type, renderer_context
        )


def view_has_errors(view):
    """Return True if view has errors."""
    try:
        code = str(view.response.status_code)
    except (AttributeError, ValueError):
        return False
    return code.startswith('4') or code.startswith('5')


def format_errors(data):
    """Format the errors.

    Take data in this format
    {
        'attributes.id': 'Invalid UUID string',
        'type': 'Value must be ServiceDelivery',
        'relationships.event': 'type event should be Event',
    }

    return a list with errors in the following format:

    [{
        'status': 400,
        'detail': 'type foobar should be Event',
        'source': {'pointer': '/data/relationships/event'}
    },
    {
        'status': 400,
        'detail': 'type foobar should be ServiceDeliveryStatus',
        'source': {'pointer': '/data/relationships/status'}
    }]

    """
    errors = []
    for k, v in data.items():
        error = {}
        path = k.replace('.', '/')
        key = f'/data/{path}'
        error['detail'] = v
        error['source'] = {'pointer': key}
        errors.append(error)
    return errors

from rest_framework import renderers


class JSONRenderer(renderers.JSONRenderer):

    media_type = 'application/vnd.api+json'
    format = 'vnd.api+json'

    def render_errors(self, data, accepted_media_type=None, renderer_context=None):
        return super(JSONRenderer, self).render(
            data, accepted_media_type, renderer_context
        )

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Produce the json to be rendered.

        data is a RepoResponse class instance.
        """
        renderer_context = renderer_context or {}
        view = renderer_context.get('view')
        if view_has_errors(view):
            data = {'errors': format_errors(data, view.response.status_code)}
            return self.render_errors(data, accepted_media_type, renderer_context)

        render_data = {'data': data.data}
        if isinstance(data.data, list):
            render_data['meta'] = data.metadata
            render_data['links'] = data.links

        return super(JSONRenderer, self).render(
            render_data, accepted_media_type, renderer_context
        )


def view_has_errors(view):
    """Return True of"""
    try:
        code = str(view.response.status_code)
    except (AttributeError, ValueError):
        pass
    else:
        if code.startswith('4') or code.startswith('5'):
            return True
    return False


def format_errors(data, status_code):
    """Format the errors.

    Take data in this format
    {
        'attributes.id': 'Invalid UUID string',
        'type': 'Value must be ServiceDelivery',
        'relationships.event': 'type event should be Event',
    }

    If one error, return:
    {
        'status': 400,
        'detail': 'type foobar should be ServiceDeliveryStatus',
        'source': {'pointer': '/data/relationships/status'}
    }


    else:

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
        key = '/data/{path}'.format(path=k.replace('.', '/'))
        error['detail'] = v
        error['source'] = {'pointer': key}
        error['status'] = status_code
        errors.append(error)
    if len(errors) > 1:
        return errors
    return errors[0]

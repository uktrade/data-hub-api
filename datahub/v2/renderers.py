from rest_framework import renderers


class JSONRenderer(renderers.JSONRenderer):

    media_type = 'application/vnd.api+json'
    format = 'vnd.api+json'

    def render_errors(self, data, accepted_media_type=None, renderer_context=None):
        return super(JSONRenderer, self).render(
            format_errors(data), accepted_media_type, renderer_context
        )

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Produce the json to be rendered.

        data is a RepoResponse class instance.
        """
        import ipdb; ipdb.set_trace()
        renderer_context = renderer_context or {}
        view = renderer_context.get('view')
        if view_has_errors(view):
            self.render_errors(data, accepted_media_type, renderer_context)

        render_data = {'data': data.data}
        if isinstance(data.data, list):
            render_data['meta'] = data.metadata
            render_data['links'] = data.links

        return super(JSONRenderer, self).render(
            render_data, accepted_media_type, renderer_context
        )


def view_has_errors(view):
    try:
        code = str(view.response.status_code)
    except (AttributeError, ValueError):
        pass
    else:
        if code.startswith('4') or code.startswith('5'):
            return True
    return False


def format_errors(data):
    pass
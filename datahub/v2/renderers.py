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
        renderer_context = renderer_context or {}
        repo_data = data
        data = repo_data.data
        render_data = {'data': data}
        if isinstance(data, list):
            render_data['meta'] = repo_data.metadata
            render_data['links'] = repo_data.links

        return super(JSONRenderer, self).render(
            render_data, accepted_media_type, renderer_context
        )


def format_errors(data):
    pass
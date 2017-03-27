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
        request = renderer_context.get('request')
        view = renderer_context.get('view')
        render_data = {'data': data.data}
        if isinstance(data, list):
            render_data['meta'] = self.build_meta(
                data_size=len(data)
            )
            render_data['links'] = self.build_list_view_links()
        return super(JSONRenderer, self).render(
            render_data, accepted_media_type, renderer_context
        )

    def build_meta(self, data_size):
        """Meta to be returned in the list view."""
        return {
            'pagination': {
                'count': data_size,
                'limit': 100,
                'offset': 0
            }
        }

    def build_list_view_links(self):
        """Links list view, for pagination."""
        return {
            'first': '',
            'last': '',
            'next': '',
            'prev': ''
        }

def format_errors(data):
    pass
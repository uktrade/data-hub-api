from django.urls import reverse
from rest_framework import status

from datahub.core.test_utils import AdminTestMixin
from datahub.investment.project.notification.models import NotificationInnerTemplate


class TestNotificaitonInnerTemplateAdmin(AdminTestMixin):
    """Tests for notification inner template django admin."""

    def test_admin_update_inner_template_retains_newline(self):
        """Test updating inner template will retain a newline."""
        notification_type = NotificationInnerTemplate.NotificationType.NOT_SET
        template = NotificationInnerTemplate.objects.create(
            content='test',
            notification_type=notification_type,
        )
        app_label = template._meta.app_label
        model_name = template._meta.model_name
        url = reverse(
            f'admin:{app_label}_{model_name}_change',
            args=(template.pk,),
        )
        response = self.client.get(url, follow=True)
        assert response.status_code == status.HTTP_200_OK

        data = {
            'id': template.id,
            'content': f'{template.content}\r\n',
            'notification_type': template.notification_type,
            '_save': 'Save',
        }

        response = self.client.post(url, data, follow=True)
        assert response.status_code == status.HTTP_200_OK

        template.refresh_from_db()
        assert template.content == 'test\r\n'

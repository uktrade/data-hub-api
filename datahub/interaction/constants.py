from enum import Enum

from datahub.core.constants import Constant


class CommunicationChannel(Enum):
    """Communication channels."""

    email_website = Constant('Email/Website', '70c226d7-5d95-e211-a939-e4115bead28a')
    face_to_face = Constant('Face to Face', 'a5d71fdd-5d95-e211-a939-e4115bead28a')
    letter_fax = Constant('Letter/Fax', '74c226d7-5d95-e211-a939-e4115bead28a')
    social_media = Constant('Social Media', 'a8d71fdd-5d95-e211-a939-e4115bead28a')
    telephone = Constant('Telephone', '72c226d7-5d95-e211-a939-e4115bead28a')
    video_teleconf = Constant('Video/Teleconf.', 'a7d71fdd-5d95-e211-a939-e4115bead28a')

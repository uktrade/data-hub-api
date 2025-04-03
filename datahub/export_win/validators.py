from rest_framework import serializers


class DuplicateContributingAdviserValidator:
    """Validates that same contributing adviser is not supplied more than once."""

    def __call__(self, data):
        """Performs validation."""
        contributing_advisers = data.get('contributing_advisers', [])
        if not contributing_advisers:
            contributing_advisers = data.get('advisers', [])

        if not contributing_advisers:
            return

        advisers = [item['adviser'] for item in contributing_advisers]
        if len(advisers) > len(set(advisers)):
            raise serializers.ValidationError(
                'A contributing adviser cannot be a duplicate.',
                code='duplicate_contributing_adviser',
            )


class DuplicateTeamMemberValidator:
    """Validates that same team member is not supplied more than once."""

    def __call__(self, data):
        """Performs validation."""
        team_members = data.get('team_members', [])
        if not team_members:
            return

        if len(team_members) > len(set(team_members)):
            raise serializers.ValidationError(
                'A team member cannot be a duplicate.',
                code='duplicate_team_member',
            )


class LeadOfficerAndContributingAdviserValidator:
    """Validates that same contributing adviser is not a lead officer."""

    def __call__(self, data):
        """Performs validation."""
        contributing_advisers = data.get('contributing_advisers', [])
        if not contributing_advisers:
            contributing_advisers = data.get('advisers', [])

        if not contributing_advisers:
            return

        lead_officer = data.get('lead_officer', None)

        if any(item['adviser'] == lead_officer for item in contributing_advisers):
            raise serializers.ValidationError(
                'A contributing adviser cannot also be lead officer.',
                code='lead_officer_as_contributing_adviser',
            )


class LeadOfficerAndTeamMemberValidator:
    """Validates that same team member is not a lead officer."""

    def __call__(self, data):
        """Performs validation."""
        team_members = data.get('team_members', [])
        if not team_members:
            return

        lead_officer = data.get('lead_officer', None)

        if lead_officer in team_members:
            raise serializers.ValidationError(
                'A team member cannot also be lead officer.',
                code='lead_officer_as_team_member',
            )


class TeamMembersAndContributingAdvisersValidator:
    """Validates that same team member is not a contributing adviser."""

    def __call__(self, data):
        """Performs validation."""
        team_members = data.get('team_members', [])
        contributing_advisers = data.get('contributing_advisers', [])
        if not contributing_advisers:
            contributing_advisers = data.get('advisers', [])

        team_member_ids = [item.id for item in team_members]
        adviser_ids = [item['adviser'].id for item in contributing_advisers]

        if set(team_member_ids) & set(adviser_ids):
            raise serializers.ValidationError(
                'A team member cannot also be a contributing adviser.',
                code='team_member_as_contributing_adviser',
            )

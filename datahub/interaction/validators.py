from django.utils.translation import gettext_lazy
from rest_framework import serializers

from datahub.core.validate_utils import DataCombiner
from datahub.interaction.models import Interaction, ServiceAnswerOption


class ServiceAnswersValidator:
    """Validates service answers."""

    requires_context = True
    required_message = gettext_lazy('This field is required.')
    question_does_not_exist = gettext_lazy('Question does not exist.')
    question_does_not_relate_message = gettext_lazy(
        'This question does not relate to selected service.',
    )
    answer_invalid_format_message = gettext_lazy('Answers have invalid format.')
    answer_not_required_message = gettext_lazy('Answers not required for given service value.')
    answer_does_not_exist_message = gettext_lazy(
        'The selected answer option is not valid for this question.',
    )
    only_one_answer_per_question_message = gettext_lazy(
        'Only one answer can be selected for this question.',
    )

    def __call__(self, data, serializer):
        """Performs validation."""
        data_combiner = DataCombiner(serializer.instance, data)

        service = data_combiner.get_value('service')
        service_answers = data_combiner.get_value('service_answers')

        expected_questions = {
            str(question.pk): question
            for question in service.interaction_questions.all()
        } if service else {}

        self._validate_type_and_truthiness(expected_questions, service_answers)

        if service_answers is not None:
            self._validate_questions(expected_questions, service_answers)

    @classmethod
    def _validate_type_and_truthiness(cls, expected_questions, service_answers):
        if service_answers is not None and not isinstance(service_answers, dict):
            raise serializers.ValidationError({
                'service_answers': cls.answer_invalid_format_message,
            })

        if not expected_questions and service_answers:
            raise serializers.ValidationError({
                'service_answers': cls.answer_not_required_message,
            })

        if expected_questions and not service_answers:
            raise serializers.ValidationError({
                'service_answers': cls.required_message,
            })

    @classmethod
    def _validate_questions(cls, expected_questions, service_answers):
        errors = {}

        # Add errors for any unanswered questions
        for question_id in expected_questions.keys() - service_answers.keys():
            errors[question_id] = [cls.required_message]

        # Add errors for any unexpected questions in provided data
        for question_id in service_answers.keys() - expected_questions.keys():
            errors[question_id] = [cls.question_does_not_relate_message]

        # Validate the answer options provided for each question
        for question_id in service_answers.keys() & expected_questions.keys():
            answer_options = service_answers[question_id]

            try:
                cls._validate_question_answers(question_id, answer_options)
            except serializers.ValidationError as exc:
                cls._add_errors_to_dict(errors, exc)

        if errors:
            raise serializers.ValidationError(errors)

    @classmethod
    def _validate_question_answers(cls, question_id, provided_answer_options):
        if len(provided_answer_options) == 0:
            raise serializers.ValidationError({
                question_id: cls.required_message,
            })

        if len(provided_answer_options) > 1:
            raise serializers.ValidationError({
                question_id: cls.only_one_answer_per_question_message,
            })

        (answer_option_id,) = provided_answer_options

        answer_option_is_valid = ServiceAnswerOption.objects.filter(
            id=answer_option_id,
            question_id=question_id,
        ).exists()

        if not answer_option_is_valid:
            raise serializers.ValidationError({
                answer_option_id: cls.answer_does_not_exist_message,
            })

    @staticmethod
    def _add_errors_to_dict(target, exc):
        normalised_errors = serializers.as_serializer_error(exc)

        for field, source_errors in normalised_errors.items():
            target_errors = target.setdefault(field, [])
            target_errors.extend(source_errors)


class ContactsBelongToCompanyValidator:
    """Validates that an interaction's contacts belong to the interaction's company."""

    requires_context = True

    def __call__(self, data, serializer):
        """
        Performs validation.

        TODO: this method has do be simplified once `company` field is removed.
        """
        instance = serializer.instance
        company_has_changed = not instance or (
            'company' in data and data['company'] != instance.company
        )
        companies_have_changed = not instance or (
            'companies' in data and set(data['companies']) != set(instance.companies.all())
        )

        contacts_have_changed = not instance or (
            'contacts' in data and set(data['contacts']) != set(instance.contacts.all())
        )

        if not (company_has_changed or companies_have_changed or contacts_have_changed):
            return

        combiner = DataCombiner(instance, data)
        company = combiner.get_value('company')

        if company_has_changed and company:
            companies = (company,)
        else:
            companies = combiner.get_value_to_many('companies')

        contacts = combiner.get_value_to_many('contacts')
        if any(contact.company not in companies for contact in contacts):
            raise serializers.ValidationError(
                'The interaction contacts must belong to the specified company.',
                code='inconsistent_contacts_and_company',
            )


class StatusChangeValidator:
    """
    Validates that an interaction's status cannot change from complete back to
    draft.  An interaction with status='complete' means that the interaction
    occurred successfully and any extra details for it have been logged.
    """

    requires_context = True

    def __call__(self, data, serializer):
        """
        Performs validation.
        """
        instance = serializer.instance
        if not instance:
            return
        existing_interaction_complete = instance.status == Interaction.Status.COMPLETE
        combiner = DataCombiner(instance, data)
        new_status = combiner.get_value('status')
        update_changes_status = new_status != instance.status
        if existing_interaction_complete and update_changes_status:
            raise serializers.ValidationError(
                'The status of a complete interaction cannot change.',
                code='complete_interaction_status_cannot_change',
            )


class DuplicateExportCountryValidator:
    """
    Validates that same country is not supplied more than once
    within list of export_countries.
    """

    def __call__(self, data):
        """Performs validation."""
        export_countries = data.get('export_countries', None)

        if not export_countries:
            return

        countries = [item['country'] for item in export_countries]
        if len(countries) > len(set(countries)):
            raise serializers.ValidationError(
                'A country that was discussed cannot be entered in multiple fields.',
                code='duplicate_export_country',
            )

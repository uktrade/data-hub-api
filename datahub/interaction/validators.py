from collections import defaultdict
from functools import lru_cache

from rest_framework.exceptions import ValidationError

from datahub.core.validate_utils import DataCombiner
from datahub.interaction.models import (
    Interaction,
    ServiceAdditionalQuestion,
    ServiceAnswerOption,
    ServiceQuestion,
)


class ServiceAnswersValidator:
    """Validates service answers."""

    required_message = 'This field is required.'
    question_does_not_exist = 'Question does not exist.'
    question_does_not_relate_message = 'This question does not relate to selected service.'
    answer_invalid_format_message = 'Answers have invalid format.'
    answer_not_required_message = 'Answers not required for given service value.'
    answer_does_not_exist_message = 'This answer does not exist.'
    additional_question_does_not_exist_message = 'This additional answer does not exist.'
    additional_question_does_not_belong_to_answer_message = \
        'Additional question does not belong to answer.'
    additional_question_value_is_not_a_number = 'This field needs to have a number.'
    only_one_answer_per_question_message = 'Only one answer can be selected for this question.'

    def __init__(self):
        """Initialises the validator."""
        self.instance = None

    def set_context(self, serializer):
        """Saves a reference to the model object."""
        self.instance = serializer.instance

    def _get_service_answers(self, service, data_combiner):
        """Return service answers if valid."""
        # check format of service answers
        service_answers = data_combiner.get_value('service_answers')

        if service_answers and not isinstance(service_answers, dict):
            raise ValidationError({
                'service_answers': self.answer_invalid_format_message,
            })

        # check if service answers shouldn't be provided
        has_service_answers = bool(service_answers)
        if service is None or service.interaction_questions.count() == 0:
            if has_service_answers:
                raise ValidationError({
                    'service_answers': self.answer_not_required_message,
                })
            return None

        if service.interaction_questions.count() > 0 and not has_service_answers:
            raise ValidationError({
                'service_answers': self.required_message,
            })

        return service_answers

    def _validate_answer_options(self, db_service_question, answer_options, errors):
        """Validate answer options."""
        if len(answer_options.keys()) > 1:
            errors[db_service_question.id] = [self.only_one_answer_per_question_message]
            return errors

        for answer_option_id, additional_questions in answer_options.items():
            db_answer_option = self._get_answer_option(answer_option_id)
            if db_answer_option is None:
                errors[answer_option_id] = [self.answer_does_not_exist_message]
                break

            errors = self._validate_additional_questions(
                db_answer_option,
                additional_questions,
                errors,
            )

        return errors

    def _validate_additional_questions(self, db_answer_option, additional_questions, errors):
        """Validate additional questions."""
        required_additional_questions = [
            str(additional_question_id) for additional_question_id in
            db_answer_option.additional_questions.filter(is_required=True)
        ]

        for additional_question_id, value in additional_questions.items():
            db_additional_question = self._get_additional_question(
                additional_question_id,
            )
            if db_additional_question is None:
                errors[additional_question_id] = [
                    self.additional_question_does_not_exist_message,
                ]
                break

            if additional_question_id in required_additional_questions:
                required_additional_questions.remove(additional_question_id)

            if db_additional_question.answer_option_id != db_answer_option.id:
                errors[additional_question_id] = [
                    self.additional_question_does_not_belong_to_answer_message,
                ]
                break

            # check if value is valid for given type
            if db_additional_question.type == 'money' and value != '':
                try:
                    int(value)
                except ValueError:
                    errors[additional_question_id] = [
                        self.additional_question_value_is_not_a_number,
                    ]

        for required_additional_question_id in required_additional_questions:
            errors[required_additional_question_id] = [self.required_message]

        return errors

    def __call__(self, data):
        """Performs validation."""
        data_combiner = DataCombiner(self.instance, data)
        service = data_combiner.get_value('service')

        # check format of service answers
        service_answers = self._get_service_answers(service, data_combiner)
        if service_answers is None:
            return

        # check if all required answers are provided
        required_question_ids = [
            str(question_id) for question_id in
            service.interaction_questions.values_list('id', flat=True)
        ]

        errors = defaultdict(list)

        for service_question_id, answer_options in service_answers.items():
            db_service_question = self._get_question(service_question_id)
            if db_service_question is None:
                errors[service_question_id] = [self.question_does_not_exist]
                break

            try:
                required_question_ids.remove(service_question_id)
            except ValueError:
                errors[service_question_id] = [self.question_does_not_relate_message]
                break

            errors = self._validate_answer_options(db_service_question, answer_options, errors)

        for required_question_id in required_question_ids:
            errors[required_question_id] = [self.required_message]

        if errors:
            raise ValidationError(errors)

    @staticmethod
    @lru_cache(maxsize=None)
    def _get_question(service_question_id):
        return ServiceQuestion.objects.filter(id=service_question_id).first()

    @staticmethod
    @lru_cache(maxsize=None)
    def _get_answer_option(answer_option_id):
        return ServiceAnswerOption.objects.filter(id=answer_option_id).first()

    @staticmethod
    @lru_cache(maxsize=None)
    def _get_additional_question(additional_question_id):
        return ServiceAdditionalQuestion.objects.filter(id=additional_question_id).first()


class ContactsBelongToCompanyValidator:
    """Validates that an interaction's contacts belong to the interaction's company."""

    def __init__(self):
        """Initialises the validator."""
        self.instance = None

    def set_context(self, serializer):
        """Saves a reference to the model object."""
        self.instance = serializer.instance

    def __call__(self, data):
        """Performs validation."""
        company_has_changed = not self.instance or (
            'company' in data and data['company'] != self.instance.company
        )

        contacts_have_changed = not self.instance or (
            'contacts' in data and set(data['contacts']) != set(self.instance.contacts.all())
        )

        if not (company_has_changed or contacts_have_changed):
            return

        combiner = DataCombiner(self.instance, data)
        company = combiner.get_value('company')
        contacts = combiner.get_value_to_many('contacts')

        if any(contact.company != company for contact in contacts):
            raise ValidationError(
                'The interaction contacts must belong to the specified company.',
                code='inconsistent_contacts_and_company',
            )


class StatusChangeValidator:
    """
    Validates that an interaction's status cannot change from complete back to
    draft.  An interaction with status='complete' means that the interaction
    occurred successfully and any extra details for it have been logged.
    """

    def __init__(self):
        """
        Initialises the validator.
        """
        self.instance = None

    def set_context(self, serializer):
        """
        Saves a reference to the model object.
        """
        self.instance = serializer.instance

    def __call__(self, data):
        """
        Performs validation.
        """
        if not self.instance:
            return
        existing_interaction_complete = self.instance.status == Interaction.STATUSES.complete
        combiner = DataCombiner(self.instance, data)
        new_status = combiner.get_value('status')
        update_changes_status = new_status != self.instance.status
        if existing_interaction_complete and update_changes_status:
            raise ValidationError(
                'The status of a complete interaction cannot change.',
                code='complete_interaction_status_cannot_change',
            )

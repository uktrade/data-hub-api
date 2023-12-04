def validate_single_task_relationship(investment_project, company, exception_class):
    if investment_project and company:
        raise exception_class('You cannot assign both a company and investment project to a task')

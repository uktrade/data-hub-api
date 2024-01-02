def validate_single_task_relationship(investment_project, company, interaction, exception_class):
    relationship_count = 0
    if company:
        relationship_count += 1
    if investment_project:
        relationship_count += 1
    if interaction:
        relationship_count += 1

    if relationship_count > 1:
        raise exception_class(
            'You can assign either a company, investment project or interaction to a task'
        )

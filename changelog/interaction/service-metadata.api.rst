``GET /metadata/service/``: The ``interaction_questions`` field was added to responses. It contains a representation of service questions and answer options from ``ServiceQuestion`` and ``ServiceAnswerOption`` models. It is an array of following format::

    [ # Array of ServiceQuestion
        {
            'id': <uuid>,
            'name: <str>,
            'disabled_on': <datetime>,
            'answer_options': [ # Array of ServiceAnswerOption
                {
                    'id': <uuid>,
                    'name': <str>,
                    'disabled_on': <datetime>
                },
                ...
            ]
        },
        ...
    ]


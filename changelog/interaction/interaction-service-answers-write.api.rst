``POST /v3/interaction``, ``PATCH /v3/interaction/<id>``: An optional (depending on selected Service) ``service_answers`` field was added to request bodies.

The ``service_answers`` body is expected to be in the following format::



    {
        "<uuid>": {  # service question id
            "<uuid>": {  # service answer option id
                "<uuid>": "<str|int>",  # service additional question id
                "<uuid>>: "<str|int>",
                ...
            }
        },
        ...
    }



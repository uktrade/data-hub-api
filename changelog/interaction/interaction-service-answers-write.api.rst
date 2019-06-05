``POST /v3/interaction``, ``PATCH /v3/interaction/<id>``: An optional (depending on selected Service) ``service_answers`` field was added to request bodies.

The ``service_answers`` body is expected to be in the following format::



    {
        "<service question ID>": {
            "<service answer option ID>": {
                # body reserved for future use
            }
        },
        ...
    }



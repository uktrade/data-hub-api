from rest_framework import viewsets, status
from rest_framework.response import Response
from api.models.interaction import Interaction
from api.serializers.interactionserializer import InteractionSerializer, InteractionSaveSerializer
from api.services.searchservice import delete_for_source_id, search_item_from_interaction


class InteractionViewSet(viewsets.ModelViewSet):
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer

    def create(self, request, **kwargs):
        # Create a model object, validate and save
        serializer = InteractionSaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_interaction = serializer.save()

        search_item = search_item_from_interaction(new_interaction)
        search_item.save()

        # send back the newly record and inform the user if all is well.
        response_serializer = InteractionSaveSerializer(new_interaction)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = InteractionSaveSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        interaction = serializer.save()
        delete_for_source_id(interaction.id)

        search_item = search_item_from_interaction(interaction)
        search_item.save()

        return Response(serializer.data)

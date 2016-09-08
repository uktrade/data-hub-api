from rest_framework import viewsets, status
from rest_framework.response import Response
from api.models.contact import Contact
from api.serializers import ContactSerializer
from api.services.searchservice import delete_for_source_id, search_item_from_contact


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def create(self, request, **kwargs):
        # Create a model object, validate and save
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_contact = serializer.save()

        search_item = search_item_from_contact(new_contact)
        search_item.save()

        # send back the newly record and inform the user if all is well.
        response_serializer = self.get_serializer(new_contact)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        contact = serializer.save()
        delete_for_source_id(contact.id)

        search_item = search_item_from_contact(contact)
        search_item.save()

        return Response(serializer.data)

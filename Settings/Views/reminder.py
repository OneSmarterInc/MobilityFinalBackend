from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status

from ..ser import ReminderSerializer
from ..models import Reminder
class ReminderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Placeholder for getting reminders
        reminders = Reminder.objects.filter(log_email=request.user.email) 
        reminders = ReminderSerializer(reminders, many=True).data

        return Response({"data": reminders}, status=status.HTTP_200_OK)

    def post(self, request):
        # Placeholder for creating a reminder
        data = request.data  # This should be validated and processed
        print("Data received for reminder creation:", data)
        reminder = Reminder.objects.create(**data)
        return Response({"message": "Reminder created successfully", "data": data}, status=status.HTTP_201_CREATED)
    def put(self, request, pk):
        # Placeholder for updating a reminder
        try:
            reminder = Reminder.objects.get(id=pk)

            for attr, value in request.data.items():
                print(f"Updating {attr} to {value} for reminder with ID {pk}")
                setattr(reminder, attr, value)
            reminder.save()
            return Response({"message": "Reminder updated successfully"}, status=status.HTTP_200_OK)
        except Reminder.DoesNotExist:
            return Response({"error": "Reminder not found"}, status=status.HTTP_404_NOT_FOUND)
        

    def delete(self, request, pk):
        try:
            reminder = Reminder.objects.get(id=pk)
            reminder.delete()
            return Response({"message": "Reminder deleted successfully"}, status=status.HTTP_200_OK)
        except Reminder.DoesNotExist:
            return Response({"message": "Reminder not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"An error occurred while deleting the reminder: {e}")
            return Response({"message": "An error occurred while deleting the reminder"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
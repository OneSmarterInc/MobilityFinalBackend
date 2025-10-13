from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status

from ..ser import ReminderSerializer
from ..models import Reminder
from Dashboard.ModelsByPage.DashAdmin import UserRoles
from authenticate.views import saveuserlog
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
        roles = data.pop('to_roles', [])
        to_roles = list(UserRoles.objects.filter(name__in=roles).values_list('id', flat=True))
        reminder = Reminder.objects.create(company=request.user.company,**data)
        
        reminder.save()
        saveuserlog(request.user, "Created reminder.")
        return Response({"message": "Reminder created successfully", "data": data}, status=status.HTTP_201_CREATED)
    def put(self, request, pk):
        # Placeholder for updating a reminder
        try:
            data = request.data
            roles = data.pop('to_roles', [])
            to_roles = list(UserRoles.objects.filter(name__in=roles).values_list('id', flat=True))
            reminder = Reminder.objects.get(id=pk)
            for attr, value in data.items():
                print(f"Updating {attr} to {value} for reminder with ID {pk}")
                setattr(reminder, attr, value)
            reminder.to_roles.set(to_roles)
            reminder.save()
            saveuserlog(request.user, "Reminder updated.")
            return Response({"message": "Reminder updated successfully"}, status=status.HTTP_200_OK)
        except Reminder.DoesNotExist:
            return Response({"error": "Reminder not found"}, status=status.HTTP_404_NOT_FOUND)
        

    def delete(self, request, pk):
        try:
            reminder = Reminder.objects.get(id=pk)
            reminder.delete()
            saveuserlog(request.user, "Reminder deleted.")
            return Response({"message": "Reminder deleted successfully"}, status=status.HTTP_200_OK)
        except Reminder.DoesNotExist:
            return Response({"message": "Reminder not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"An error occurred while deleting the reminder: {e}")
            return Response({"message": "An error occurred while deleting the reminder"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
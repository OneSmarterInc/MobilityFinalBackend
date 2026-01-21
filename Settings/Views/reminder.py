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

    def get(self, request, *args, **kwargs):
        # Placeholder for getting reminders
        reminders = Reminder.objects.filter(log_email=request.user.email) 
        reminders = ReminderSerializer(reminders, many=True).data
        return Response({"data": reminders}, status=status.HTTP_200_OK)

    def post(self, request):
        # Placeholder for creating a reminder
        data = request.data  # This should be validated and processed
        roles = data.pop('to_roles', [])
        reminder_for = data.pop('reminder_for')
        if reminder_for == "all":
            roles = data.pop('to_roles', [])
            to_roles = list(UserRoles.objects.filter(name__in=roles).values_list('id', flat=True))
        else:
            to_roles = [request.user.designation.id]
        reminder = Reminder.objects.create(company=request.user.company,**data)
        reminder.to_roles.set(to_roles)
        reminder.save()
        saveuserlog(request.user, "Created reminder.")
        return Response({"message": "Reminder created successfully", "data": data}, status=status.HTTP_201_CREATED)
    def put(self, request, pk):
        # Placeholder for updating a reminder
        try:
            data = request.data
            print(data)
            reminder_for = data.pop('reminder_for')
            if reminder_for == "all":
                roles = data.pop('to_roles', [])
                to_roles = list(UserRoles.objects.filter(name__in=roles).values_list('id', flat=True))
            else:
                to_roles = [request.user.designation.id]
            reminder = Reminder.objects.get(id=pk)
            print("to==",to_roles)
            for attr, value in data.items():
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
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from OnBoard.Company.models import Company
from Dashboard.ModelsByPage.DashAdmin import UserRoles
from django.utils import timezone

class CheckUserReminderView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        company_name = request.GET.get('company')
        role_name = request.GET.get('role')

        # Get company and role objects
        company = Company.objects.filter(Company_name=company_name).first()
        role = UserRoles.objects.filter(name=role_name).first()

        if not (company and role):
            return Response({"message": "Undefined attributes!"}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.localtime(timezone.now())
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        current_day = now.strftime("%A").lower()

        print(current_date, current_date, current_time, current_day)

        # Fetch all reminders for this company & role
        reminders = Reminder.objects.filter(company=company, to_roles=role)

        if not reminders.exists():
            return Response({"data": False}, status=status.HTTP_200_OK)

        # --- 1️⃣ CUSTOM Reminder ---
        custom = reminders.filter(
            reminder_type="custom",
            date=current_date,
            time=current_time
        ).first()
        if custom:
            return self._response(custom, date=custom.date, time=custom.time)

        # --- 2️⃣ DAILY Reminder ---
        daily = reminders.filter(
            reminder_type="daily",
            time=current_time
        ).first()
        if daily:
            return self._response(daily, date=daily.date, time=daily.time)

        # --- 3️⃣ MONTHLY Reminder ---
        monthly = reminders.filter(
            reminder_type="monthly",
            date=current_date,
            time=current_time
        ).first()
        if monthly:
            return self._response(monthly, date=monthly.date, time=monthly.time)

        # --- 4️⃣ WEEKLY Reminder ---
        all_weekly = reminders.filter(reminder_type="weekly")
        for weekly in all_weekly:
            for week_rem in weekly.weekly_Reminders:
                day = week_rem.get("day")
                time = week_rem.get("time")
                print(day, time)
                if day == current_day and time == current_time:
                    # Match time as well if provided
                    return self._response(weekly, date=current_date, time=current_time)

        return Response({"data": False}, status=status.HTTP_200_OK)
    
    def _response(self, reminder, date, time):
        """Helper to format consistent response"""
        reminder_data = {
            "reminder_type":reminder.reminder_type,
            "title": reminder.title,
            "description": reminder.description,
            "date":date,
            "time":time
        }
        return Response({"data": reminder_data}, status=status.HTTP_200_OK)
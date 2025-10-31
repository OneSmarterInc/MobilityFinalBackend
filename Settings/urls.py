from django.urls import path, include
from .Views.reminder import ReminderView
from .Views.ticket import TicketView, TicketChatView
from .Views.History import BanHistoryView, WirelessHistoryView
from .Views.managepermissions import ManagePermissionsView
from .Views.reminder import CheckUserReminderView
urlpatterns = [
    # Reminder URLs
    path('reminders/', ReminderView.as_view(), name='reminder'),
    path('reminders/<str:pk>/', ReminderView.as_view(), name='reminder-detail'),
    # Ticket URLs
    path('tickets/', TicketView.as_view(), name='ticket'),
    path('tickets/<str:pk>/', TicketView.as_view(), name='ticket-detail'),

    path('ticket-chats/<str:pk>/', TicketChatView.as_view(), name='ticket-chat-detail'),
    path('wireless-history/<wn>/', WirelessHistoryView.as_view(), name='wireless-history'),
    path('ban-history/<ban>/', BanHistoryView.as_view(), name='ban-history'),

    path('permissions-by-company/<company>/', ManagePermissionsView.as_view(), name='manage-permissions'),
    path('check-reminder/', CheckUserReminderView.as_view(), name='check-reminder'),
]
from django.urls import path, include
from .Views.reminder import ReminderView
from .Views.ticket import TicketView, TicketChatView
urlpatterns = [
    # Reminder URLs
    path('reminders/', ReminderView.as_view(), name='reminder'),
    path('reminders/<str:pk>/', ReminderView.as_view(), name='reminder-detail'),
    # Ticket URLs
    path('tickets/', TicketView.as_view(), name='ticket'),
    path('tickets/<str:pk>/', TicketView.as_view(), name='ticket-detail'),

    path('ticket-chats/<str:pk>/', TicketChatView.as_view(), name='ticket-chat-detail'),

]
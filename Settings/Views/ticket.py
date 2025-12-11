from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ..models import Ticket
from authenticate.models import PortalUser
from ..ser import TicketSerializer, PortalUserSerializer
from sendmail import send_ticket
from authenticate.views import saveuserlog
class TicketView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        # Placeholder for getting tickets
        tickets = Ticket.objects.all()  
        user = request.user
        if request.GET.get('action') == "get-user-emails":
            user_emails = PortalUser.objects.filter(organization=user.organization) if user.organization else PortalUser.objects.filter(company=user.company)
            user_emails = user_emails.exclude(is_staff=True)
            user_emails = PortalUserSerializer(user_emails, many=True).data
            return Response({"emails": user_emails}, status=status.HTTP_200_OK)

        tickets = TicketSerializer(tickets, many=True).data
        return Response({"data": tickets}, status=status.HTTP_200_OK)
    def post(self, request):
        # Placeholder for creating a ticket
        data = request.data
        print("Data received for ticket creation:", data)
        ticket = Ticket.objects.create(**data)
        send_ticket((data['assign_email'],data['user_email'],"gauravdhale09@gmail.com" ), data['sub_company'], data['vendor'], data['account_no'], data['message'], data['description'], data['priority']) #, ticket_number=ticket.ticket_number)
    
        saveuserlog(request.user, "Ticket created.")
    
        return Response({"message": "Ticket created successfully", "ticket_id": ticket.id}, status=status.HTTP_201_CREATED)
    def put(self, request, pk):
        # Placeholder for updating a ticket
        try:
            ticket = Ticket.objects.get(id=pk)
            print(f"Updating ticket with ID {pk} with data: {request.data}")
            if "action" in request.data:
                if request.data["action"] == "update-ticket-status":
                    sts = request.data.pop('status')
                    print(f"Updating ticket status to: {sts}")
                    if sts == "in_process":
                        ticket.in_process, ticket.is_hold, ticket.is_resolved, ticket.is_closed = True,False,False, False
                    if sts == "on_hold":
                        ticket.is_hold,ticket.in_process, ticket.is_resolved, ticket.is_closed = True,False,False, False
                    if sts == "resolved":
                        ticket.is_resolved,ticket.is_hold,ticket.in_process, ticket.is_closed = True, False, False, False
                    if sts == "closed":
                        ticket.is_closed, ticket.is_hold, ticket.is_resolved, ticket.in_process = True, False, False, False
                if request.data["action"] == "update-decription":
                    print(f"Updating ticket description to: {request.data['description']}")
                    ticket.description = request.data['description']
        
            # for attr, value in request.data.items():
            #     print(f"Updating {attr} to {value} for ticket with ID {pk}")
            #     setattr(ticket, attr, value)
            ticket.save()
            saveuserlog(request.user, "Ticket updated.")
            return Response({"message": "Ticket updated successfully"}, status=status.HTTP_200_OK)
        except Ticket.DoesNotExist:
            return Response({"message": "Ticket not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"An error occurred while updating the ticket: {e}")
            return Response({"message": "An error occurred while updating the ticket"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def delete(self, request, pk):
        # Placeholder for deleting a ticket
        try:
            ticket = Ticket.objects.get(id=pk)
            ticket.delete()
            saveuserlog(request.user, "Ticket deleted.")
            return Response({"message": "Ticket deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Ticket.DoesNotExist:
            return Response({"message": "Ticket not found"}, status=status.HTTP_404_NOT_FOUND)
        

class TicketChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        # Placeholder for getting a ticket's chat
        try:
            ticket = Ticket.objects.get(id=pk)
            chat = TicketSerializer(ticket).data
            return Response({"data": chat}, status=status.HTTP_200_OK)
        except Ticket.DoesNotExist:
            return Response({"message": "Ticket not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"An error occurred while retrieving the chat: {e}")
            return Response({"message": "An error occurred while retrieving the chat"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, pk):
        try:
            ticket = Ticket.objects.get(id=pk)
            sender = request.data.get('sender', request.user.email)
            message = request.data.get('message', '')
            if not message:
                return Response({"message": "Message cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

            ticket.add_message_to_chat(sender, message)
            return Response({"message": "Message added to chat successfully"}, status=status.HTTP_200_OK)
        except Ticket.DoesNotExist:
            return Response({"message": "Ticket not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"An error occurred while adding a message to the chat: {e}")
            return Response({"message": "An error occurred while adding a message to the chat"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
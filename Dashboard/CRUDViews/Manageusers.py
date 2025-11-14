from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ..Serializers.promange import ProfileShowSerializer
from ..ModelsByPage.ProfileManage import Profile


from OnBoard.Organization.models import Organizations
from ..Serializers.manageusers import showOrgsSerializer, UserRoleShowSerializer
from Dashboard.ModelsByPage.DashAdmin import UserRoles
from authenticate.views import saveuserlog
from authenticate.models import PortalUser

class ManageUsersView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,pk=None, *args, **kwargs):
        if pk:
            users = Profile.objects.filter(id=pk)
            if not users.exists():
                return Response({"message":"user not found!"},status=status.HTTP_400_BAD_REQUEST)
            users = users[0]
            users_serializer = ProfileShowSerializer(users)
        else:
            users = Profile.objects.all()
            users_serializer = ProfileShowSerializer(users, many=True)
        userroles = UserRoleShowSerializer(UserRoles.objects.exclude(name="Superadmin"), many=True)
        orgs = Organizations.objects.filter(company=request.user.company)
        orgs_serializer = showOrgsSerializer(orgs, many=True)
        return Response({"data":users_serializer.data, "organizations":orgs_serializer.data, "roles":userroles.data})
    
    def put(self, request, pk, *args, **kwargs):
        data = request.data
        print(pk)
        user = PortalUser.objects.filter(id=pk)
        print(data)
        if not user:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        role = UserRoles.objects.filter(id=data.get('role')).first()
        if not role.exists():
            return Response({"message": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            role = role.first()
            user.designation = role
            user.save()
            saveuserlog(request.user, f"user profile {user.email} updated.")
            return Response({"message": "User Updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"message":"Unable to update user."},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk, *args, **kwargs):
        try:
            user = Profile.objects.get(id=pk)
            email = user.email
            user.delete()
            saveuserlog(request.user, f"user profile {email} deleted.")
            return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": "Unable to delete user."}, status=status.HTTP_400_BAD_REQUEST)
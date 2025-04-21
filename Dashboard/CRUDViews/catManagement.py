from Dashboard.ModelsByPage.cat import BaselineCategories
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ..Serializers.cat import catserializer

from rest_framework.permissions import IsAuthenticated
class CategoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request,pk=None, *args, **kwargs):
        if pk:
            obj = BaselineCategories.objects.filter(id=pk)
            obj = obj.first() if obj else None 
            if BaselineCategories.DoesNotExist():
                return Response({"message": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
            ser = catserializer(obj)
        else:
            objs = BaselineCategories.objects.all()
            ser = catserializer(objs,many=True)
        return Response({"data":ser.data}, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        data = request.data
        print(data)
        if BaselineCategories.objects.filter(name=request.data["category"]).exists():
            return Response({"message": "Baseline category with this name already exists!"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            ser = catserializer(data=data)
            if ser.is_valid():
                ser.save()
                return Response({"message" : "new Category created successfully!"}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message":str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request,pk, *args, **kwargs):
        try:
            obj = BaselineCategories.objects.filter(id=pk)[0]
        except BaselineCategories.DoesNotExist():
            return Response({"message": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        data = request.data
        ser = catserializer(obj, data=data)
        if ser.is_valid():
            ser.save()
            return Response({"message" : "Category updated successfully!"}, status=status.HTTP_200_OK)
        else:
            return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request,pk, *args, **kwargs):
        try:
            category = BaselineCategories.objects.get(id=pk)
            category.delete()
            return Response({"message": "category deleted successfully!"}, status=status.HTTP_200_OK)
        except UserRoles.DoesNotExist:
            return Response({"message": "category does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message":str(e)}, status=status.HTTP_400_BAD_REQUEST)
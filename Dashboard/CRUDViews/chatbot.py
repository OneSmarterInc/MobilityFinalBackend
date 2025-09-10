from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from authenticate.models import PortalUser
from authenticate.views import saveuserlog
from bot import get_database, get_sql_from_gemini, execute_sql_query, get_response_from_gemini
from ..ModelsByPage.aimodels import BotChats
from rest_framework.permissions import IsAuthenticated
from ..Serializers.chatser import ChatSerializer


class ChatBotView(APIView):
    permission_classes = [IsAuthenticated]

    connection = None
    schema = None

    @classmethod
    def initialize_db(cls):
        """Initialize DB connection + schema once."""
        if cls.connection is None or cls.schema is None:
            cls.connection, cls.schema = get_database("db.sqlite3")

    def get(self, request, *args, **kwargs):
        chats = BotChats.objects.filter(user=request.user)
        ser = ChatSerializer(chats, many=True)
        return Response({"data":ser.data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        # Ensure DB is initialized only once
        self.initialize_db()

        data = request.data
        question = data.get("prompt")

        if not question:
            return Response(
                {"message": "Prompt is required!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            sql_query = get_sql_from_gemini(question, self.schema)

            result_df = execute_sql_query(self.connection, sql_query)

            if result_df is None or result_df.empty:
                return Response(
                    {"message": "No data found for the given query."},
                    status=status.HTTP_200_OK
                )

            response_text = get_response_from_gemini(question, result_df)

            BotChats.objects.create(
                user=request.user,
                question=question,
                response=response_text
            )


            # saveuserlog(request.user, f"Chatbot query executed: {question} | Response: {response_text}")

            return Response(
                {"response": response_text},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": f"Error processing request: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

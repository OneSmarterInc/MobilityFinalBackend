from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from authenticate.models import PortalUser
from authenticate.views import saveuserlog
# from bot import get_database, get_sql_from_gemini, execute_sql_query, get_response_from_gemini

from ..ModelsByPage.aimodels import BotChats
from rest_framework.permissions import IsAuthenticated
from ..Serializers.chatser import ChatSerializer
import pandas as pd
from Geminibot import BotClass
from OpenAIBot import OpenAIBotClass

class ChatBotView(APIView):
    permission_classes = [IsAuthenticated]

    connection = None
    schema = None


    def get(self, request, *args, **kwargs):
        chats = BotChats.objects.filter(user=request.user,billChat=None,M_analysisChat=None)
        ser = ChatSerializer(chats, many=True)
        return Response({"data":ser.data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        is_deployed = request.GET.get("is_deployed", "").lower() == "true"
        # if is_deployed: botObj = OpenAIBotClass()
        # else: botObj = BotClass()
        botObj = BotClass()
        self.connection, self.schema = botObj.init_database()
        data = request.data
        question = data.get("prompt")

        if not question:
            return Response(
                {"message": "Prompt is required!"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        chatHis=BotChats.objects.filter(user=request.user).values("question", "response", "created_at")
        df = pd.DataFrame(list(chatHis))

        try:
            instance = BotChats.objects.create(
                user=request.user,
                question=question,
            )
            is_generated, sql_query = botObj.get_general_sql_from_gemini(question, self.schema, chat_history=df)
            if not is_generated:
                instance.is_query_generated = False
                instance.response = "I need a bit more info to answer.\nCould you please elaborate more on your question."
                instance.save()
                return Response({"response":"Unable to answer the question!"},status=status.HTTP_200_OK)
            
            is_ran, result_df = botObj.run_query(conn=self.connection, sql=sql_query)

            print(result_df)
            _check, response_text = botObj.make_human_response(question, result_df, db_schema=self.schema)
            allLines = response_text.split("\n")
            questions = [line.strip() for line in allLines if line.strip().endswith("?")]
            other_lines = "\n".join([line.strip() for line in allLines if line.strip() and not line.strip().endswith("?")])
            print(is_ran, result_df)
            instance.response = other_lines
            instance.recommended_questions = questions
            if is_ran:
                instance.is_query_generated = True
                instance.is_query_ran = True
            else:
                instance.is_df_empty = True
            instance.save()   


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
        
    
    def delete(self,request,*args, **kwargs):
        try:
            objs = BotChats.objects.filter(user=request.user)
            objs.delete()
            return Response({"message":"User chats deleted successfully!"},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message":"Unable to delete user chats!"},status=status.HTTP_400_BAD_REQUEST)




# from pathlib import Path
# from django.conf import settings
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated

# from ..ModelsByPage.aimodels import BotChats
# from ..Serializers.chatser import ChatSerializer

# # Bring your helpers
# from bot import (
#     get_database,            # returns (conn, schema_json, schema_cols_only, tables_ordered)
#     get_sql_from_gemini,     # needs schema_json
#     execute_first_match,     # short-circuit executor
#     get_response_from_gemini # NL summary
# )

# # --- toggle debug quickly ---
# DEBUG_CHATBOT = False  # set True to always include internals


# class ChatBotView(APIView):
#     permission_classes = [IsAuthenticated]

#     # Class-level caches
#     connection = None
#     schema_json = None
#     schema_cols_only = None
#     tables_ordered = None

#     @classmethod
#     def initialize_db(cls):
#         """Initialize DB connection + schema once."""
#         if any(v is None for v in (cls.connection, cls.schema_json, cls.schema_cols_only, cls.tables_ordered)):
#             # Use absolute DB path; adjust to where your sqlite file actually is
#             # Example: BASE_DIR / "Bills/db.sqlite3"
#             db_path = Path(getattr(settings, "BASE_DIR", Path.cwd())) / "Bills" / "db.sqlite3"
#             cls.connection, cls.schema_json, cls.schema_cols_only, cls.tables_ordered = get_database(str(db_path))

#     def get(self, request, *args, **kwargs):
#         chats = BotChats.objects.filter(user=request.user).order_by("-id")
#         ser = ChatSerializer(chats, many=True)
#         return Response({"data": ser.data}, status=status.HTTP_200_OK)

#     def post(self, request, *args, **kwargs):
#         self.initialize_db()

#         # allow ?debug=1 to surface internals in API response
#         debug = DEBUG_CHATBOT or (request.query_params.get("debug") in ("1", "true", "yes"))

#         question = (request.data or {}).get("prompt")
#         if not question:
#             return Response({"message": "Prompt is required!"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # 1) NL -> SQL (defensive: handle empty/None)
#             sql_query = get_sql_from_gemini(question, self.schema_json)
#             if not sql_query:
#                 sql_query = "NO_SQL"

#             if sql_query == "NO_SQL":
#                 resp_text = "Sorry, that cannot be answered from the current schema."
#                 BotChats.objects.create(user=request.user, question=question, response=resp_text)
#                 payload = {"response": resp_text}
#                 if debug:
#                     payload.update({
#                         "debug": {
#                             "sql": sql_query,
#                             "schema_len": len(self.schema_json or ""),
#                             "tables_ordered": self.tables_ordered,
#                             "note": "LLM returned NO_SQL"
#                         }
#                     })
#                 return Response(payload, status=status.HTTP_200_OK)

#             # 2) Run once against the FIRST compatible table and STOP
#             df, reason, chosen_table = execute_first_match(
#                 self.connection,
#                 sql_query,
#                 self.schema_cols_only,
#                 self.tables_ordered,
#             )

#             # 3) Shape info for debugging
#             row_count = (0 if df is None else len(df.index))
#             empty = (df is not None and df.empty)

#             # 4) Turn the result into a human answer
#             response_text = get_response_from_gemini(question, df)

#             # 5) Persist chat
#             BotChats.objects.create(
#                 user=request.user,
#                 question=question,
#                 response=response_text
#             )

#             payload = {
#                 "response": response_text
#             }
#             if debug:
#                 payload.update({
#                     "debug": {
#                         "sql": sql_query,
#                         "reason": reason,
#                         "chosen_table": chosen_table,
#                         "row_count": row_count,
#                         "empty": empty,
#                         "tables_ordered": self.tables_ordered
#                     }
#                 })
#             return Response(payload, status=status.HTTP_200_OK)

#         except Exception as e:
#             # Surface the error so you’re not left guessing
#             return Response(
#                 {"message": f"Error processing request: {str(e)}"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

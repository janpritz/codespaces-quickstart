# actions.py
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from db import get_db_connection   # import your function

class ActionFetchResponse(Action):
    def name(self) -> str:
        return "action_fetch_response"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                intent = tracker.latest_message['intent'].get('name')

                cursor.execute("SELECT response FROM responses WHERE intent=%s", (intent,))
                result = cursor.fetchone()

                if result and "response_text" in result:
                    dispatcher.utter_message(text=result["response_text"])
                else:
                    dispatcher.utter_message(text="Sorry, no answer found in the database.")

        except Exception as e:
            dispatcher.utter_message(text=f"DB Error: {str(e)}")

        finally:
            connection.close()

        return []

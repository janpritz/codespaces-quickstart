from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from .db import get_db_connection

class ActionUtterVision(Action):
    def name(self) -> str:
        return "action_utter_vision"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        connection = get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT response FROM faqs WHERE intent = 'Vision'")
                results = cursor.fetchall()   # fetch ALL rows

                if results:
                    # Join all responses into one string
                    responses = "\n".join([row["response"] for row in results if row.get("response")])
                    dispatcher.utter_message(text=responses)
                else:
                    dispatcher.utter_message(
                        text="Sorry, I am not yet trained to answer this question. You can submit a ticket for further assistance."
                    )

        except Exception as e:
            dispatcher.utter_message(text=f"DB Error: {str(e)}")

        finally:
            connection.close()
        return []

class ActionUtterMission(Action):
    def name(self) -> str:
        return "action_utter_mission"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        connection = get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT response FROM faqs WHERE intent = 'Mission'")
                results = cursor.fetchall()   # fetch ALL rows

                if results:
                    # Join all responses into one string
                    responses = "\n".join([row["response"] for row in results if row.get("response")])
                    dispatcher.utter_message(text=responses)
                else:
                    dispatcher.utter_message(
                        text="Sorry, I am not yet trained to answer this question. You can submit a ticket for further assistance."
                    )

        except Exception as e:
            dispatcher.utter_message(text=f"DB Error: {str(e)}")

        finally:
            connection.close()
        return []

class ActionUtterGoals(Action):
    def name(self) -> str:
        return "action_utter_goals"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        connection = get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT response FROM faqs WHERE intent = 'Goals'")
                results = cursor.fetchall()   # fetch ALL rows

                if results:
                    # Join all responses into one string
                    responses = "\n".join([row["response"] for row in results if row.get("response")])
                    dispatcher.utter_message(text=responses)
                else:
                    dispatcher.utter_message(
                        text="Sorry, I am not yet trained to answer this question. You can submit a ticket for further assistance."
                    )

        except Exception as e:
            dispatcher.utter_message(text=f"DB Error: {str(e)}")

        finally:
            connection.close()
        return []

class ActionUtterVisionMission(Action):
    def name(self) -> str:
        return "action_utter_mission_separate"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        connection = get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                # Fetch Vision
                cursor.execute("SELECT response FROM faqs WHERE intent = 'Vision'")
                vision_results = cursor.fetchall()

                # Fetch Mission
                cursor.execute("SELECT response FROM faqs WHERE intent = 'Mission'")
                mission_results = cursor.fetchall()

                # Build the message
                message = ""

                if vision_results:
                    vision_text = "\n".join([row["response"] for row in vision_results if row.get("response")])
                    message += f"🌟 **Vision**\n{vision_text}\n\n"

                if mission_results:
                    mission_text = "\n".join([row["response"] for row in mission_results if row.get("response")])
                    message += f"🎯 **Mission**\n{mission_text}"

                if message.strip():
                    dispatcher.utter_message(text=message.strip())
                else:
                    dispatcher.utter_message(
                        text="Sorry, I am not yet trained to answer Vision and Mission. You can submit a ticket for further assistance."
                    )

        except Exception as e:
            dispatcher.utter_message(text=f"DB Error: {str(e)}")

        finally:
            if connection:
                connection.close()

        return []

class ActionUtterGoals(Action):
    def name(self) -> str:
        return "action_utter_core_values"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        connection = get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT response FROM faqs WHERE intent = 'Core Values'")
                results = cursor.fetchall()   # fetch ALL rows

                if results:
                    # Join all responses into one string
                    responses = "\n".join([row["response"] for row in results if row.get("response")])
                    dispatcher.utter_message(text=responses)
                else:
                    dispatcher.utter_message(
                        text="Sorry, I am not yet trained to answer this question. You can submit a ticket for further assistance."
                    )

        except Exception as e:
            dispatcher.utter_message(text=f"DB Error: {str(e)}")

        finally:
            connection.close()
        return []

class ActionUtterACCHymn(Action):
    def name(self) -> str:
        return "action_utter_acc_hymn"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        connection = get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT response FROM faqs WHERE intent = 'ACC Hymn'")
                results = cursor.fetchall()   # fetch ALL rows

                if results:
                    # Join all responses into one string
                    responses = "\n".join([row["response"] for row in results if row.get("response")])
                    dispatcher.utter_message(text=responses)
                else:
                    dispatcher.utter_message(
                        text="Sorry, I am not yet trained to answer this question. You can submit a ticket for further assistance."
                    )

        except Exception as e:
            dispatcher.utter_message(text=f"DB Error: {str(e)}")

        finally:
            connection.close()
        return []
    
class ActionUtterEnrollmentSchedule(Action):
    def name(self) -> str:
        return "action_utter_enrollment_schedule"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        connection = get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT response FROM faqs WHERE intent = 'Enrollment Schedule'")
                results = cursor.fetchall()   # fetch ALL rows

                if results:
                    # Join all responses into one string
                    responses = "\n".join([row["response"] for row in results if row.get("response")])
                    dispatcher.utter_message(text=responses)
                else:
                    dispatcher.utter_message(
                        text="Sorry, I am not yet trained to answer this question. You can submit a ticket for further assistance."
                    )

        except Exception as e:
            dispatcher.utter_message(text=f"DB Error: {str(e)}")

        finally:
            connection.close()
        return []

class ActionUtterOfficeOfTheRegistrar(Action):
    def name(self) -> str:
        return "action_utter_office_of_the_registrar"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        connection = get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT response FROM faqs WHERE intent = 'Office of the Registrar'")
                results = cursor.fetchall()   # fetch ALL rows

                if results:
                    # Join all responses into one string
                    responses = "\n".join([row["response"] for row in results if row.get("response")])
                    dispatcher.utter_message(text=responses)
                else:
                    dispatcher.utter_message(
                        text="Sorry, I am not yet trained to answer this question. You can submit a ticket for further assistance."
                    )

        except Exception as e:
            dispatcher.utter_message(text=f"DB Error: {str(e)}")

        finally:
            connection.close()
        return []
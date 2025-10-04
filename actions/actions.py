from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


class ActionCreateTicket(Action):
    def name(self) -> Text:
        return "create_ticket"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Get the sender ID from the messaging platform
        recipient_id = tracker.sender_id

        #baseurl
        base_url = "https://41fff35038ff.ngrok-free.app/tickets/create/"

        # Build the API URL with the recipient ID
        api_url = f"{base_url}{recipient_id}"

        # Assuming ticket creation was successful, send a success message
        dispatcher.utter_message(
            text=f"Click here to redirect to the link {api_url}."
        )
        return []


class ActionHumanHandoff(Action):
    def name(self) -> Text:
        return "action_human_handoff"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Implementation for human handoff
        dispatcher.utter_message(text="Connecting you to a human agent...")
        return []


class ActionResetTicketDecision(Action):
    def name(self) -> Text:
        return "action_reset_ticket_decision"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Reset the ticket_decision slot to None to break validation loop
        return [SlotSet("ticket_decision", None)]


class ActionResetEnrollmentCategory(Action):
    def name(self) -> Text:
        return "action_reset_enrollment_category"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Reset the enrollment_category slot to None to break validation loop
        return [SlotSet("enrollment_category", None)]


class ActionResetEnrolleeType(Action):
    def name(self) -> Text:
        return "action_reset_enrollee_type"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Reset the enrollee_type slot to None to break validation loop
        return [SlotSet("enrollee_type", None)]


class ActionResetBscrimNew(Action):
    def name(self) -> Text:
        return "action_reset_bscrim_new"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Reset the bscrim_new slot to None to break validation loop
        return [SlotSet("bscrim_new", None)]


class ActionResetDidThatHelp(Action):
    def name(self) -> Text:
        return "action_reset_did_that_help"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Reset the did_that_help slot to None to break validation loop
        return [SlotSet("did_that_help", None)]

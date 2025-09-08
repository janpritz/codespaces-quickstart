from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, Restarted

class ActionIncrementErrorCount(Action):
    def name(self):
        return "increment_error_count"

    def run(self, dispatcher, tracker, domain):
        count = tracker.get_slot("error_count") or 0
        return [SlotSet("error_count", count + 1)]

class ActionEndConversation(Action):
    def name(self):
        return "end_conversation"

    def run(self, dispatcher, tracker, domain):
        return [Restarted()]
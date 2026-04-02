from django.test import SimpleTestCase

from documents.services.chat import classify_intent


class AgentBehaviorTests(SimpleTestCase):
    def test_intent_classification(self):
        self.assertEqual(classify_intent("How much is a 40ft container?"), "pricing")
        self.assertEqual(classify_intent("Do you deliver to Texas?"), "availability")
        self.assertEqual(classify_intent("I want to place an order"), "conversion")

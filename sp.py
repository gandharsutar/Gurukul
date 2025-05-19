import json
import random

class ChatAgent:
    def __init__(self, name, avatar_url, color_theme):
        self.name = name
        self.avatar_url = avatar_url
        self.color_theme = color_theme

    def get_agent_info(self):
        return {
            "name": self.name,
            "avatar": self.avatar_url,
            "colorTheme": self.color_theme
        }

class DecisionResponse:
    def __init__(self):
        self.current_decision = ""
        self.response_text = ""

    def set_decision_and_response(self, decision, response):
        self.current_decision = decision
        self.response_text = response

    def get_decision_response(self):
        return {
            "current": self.current_decision,
            "response": self.response_text
        }

class Chatbot:
    def __init__(self, agents):
        self.agents = agents
        self.decision_response = DecisionResponse()

    def get_agents(self):
        return [agent.get_agent_info() for agent in self.agents]

    def get_decision_response(self):
        return self.decision_response.get_decision_response()

    def set_decision_and_response(self, decision, response):
        self.decision_response.set_decision_and_response(decision, response)


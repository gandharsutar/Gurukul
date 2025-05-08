import random

class DomainOrchestrator:
    def __init__(self):
        self.agents = []

    def register_agent(self, agent):
        self.agents.append(agent)
        print(f"[Orchestrator] Registered {agent.__class__.__name__}: {agent.name}")

    def run_step(self):
        print("\n--- Running Step ---")

        # Each agent performs its action
        for agent in self.agents:
            agent.act()

        # Optional: random pairwise interaction
        for agent in self.agents:
            partner = random.choice([a for a in self.agents if a != agent])
            agent.interact(partner)

    def run_simulation(self, steps=5):
        for i in range(steps):
            print(f"\n=== Step {i + 1} ===")
            self.run_step()

# Example agent stubs
class FinanceAgent:
    def __init__(self, name): self.name = name
    def act(self): print(f"{self.name} is managing finances.")
    def interact(self, other): print(f"{self.name} gives investment advice to {other.name}")

class EducationAgent:
    def __init__(self, name): self.name = name
    def act(self): print(f"{self.name} is teaching a class.")
    def interact(self, other): print(f"{self.name} is learning from {other.name}")

class WellnessAgent:
    def __init__(self, name): self.name = name
    def act(self): print(f"{self.name} is doing yoga.")
    def interact(self, other): print(f"{self.name} promotes mental health to {other.name}")

# Main simulation
if __name__ == "__main__":
    orchestrator = DomainOrchestrator()

    # Register agents
    orchestrator.register_agent(FinanceAgent("Finacial Crew"))
    orchestrator.register_agent(EducationAgent("EduMentor"))
    orchestrator.register_agent(WellnessAgent("Wellness Bot"))

    # Run the simulation
    orchestrator.run_simulation(steps=3)

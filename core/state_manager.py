class StateManager:
	def __init__(self, initial_state):
		self.state = initial_state
		self.payload = None
		self._handlers = {}

	def register(self, state_name, handler):
		self._handlers[state_name] = handler

	def transition(self, next_state, payload=None):
		self.state = next_state
		self.payload = payload

	def step(self, screen, clock):
		handler = self._handlers.get(self.state)
		if handler is None:
			self.transition("menu", None)
			return self.state

		next_state, payload = handler(screen, clock, self.payload)
		self.transition(next_state, payload)
		return self.state

def StateMachine(transition_table, state):
    while state:
        input = yield state
        for transition in transition_table[state]:
            if next_state := transition(input):
                state = next_state
                break


class Safe:
    """
    Example statemachine

    >>> safe = Safe()
    >>> next(safe.sm)
    'locked'
    >>> safe.sm.send('A')
    'locked'
    >>> safe.sm.send(5)
    'entering_code'
    >>> safe.sm.send(5)
    'entering_code'
    >>> safe.sm.send(5)
    'locked'
    >>> safe.sm.send(1)
    'entering_code'
    >>> safe.sm.send(2)
    'entering_code'
    >>> safe.sm.send(3)
    'unlocked'
    """

    def __init__(self):
        self.code = [1, 2, 3]
        self.buffer = []
        self.sm = StateMachine(
            {
                "locked": [self.digit],
                "entering_code": [self.unlock, self.error, self.digit],
                "unlocked": [self.lock],
            },
            "locked",
        )

    def unlock(self, i):
        buffer = self.buffer + [i]
        if len(buffer) == len(self.code) and buffer == self.code:
            return "unlocked"

    def error(self, i):
        buffer = self.buffer + [i]
        if len(buffer) == len(self.code) and not buffer == self.code:
            return self.lock()

    def digit(self, i):
        if isinstance(i, int) and 0 <= i <= 9:
            self.buffer.append(i)
            return "entering_code"

    def lock(self, *_):
        self.buffer = []
        return "locked"

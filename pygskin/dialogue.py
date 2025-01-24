"""A module for parsing and running dialogue scripts."""

from collections import Counter
from collections import defaultdict
from collections.abc import Callable
from collections.abc import Generator
from collections.abc import Iterator
from functools import partial
from itertools import pairwise

from pygskin.statemachine import statemachine

Action = Callable[[], None]
Dialogue = dict[str, list[dict]]


def iter_dialogue(dialogue: Dialogue, context: dict, **callbacks) -> Iterator[Action]:
    """
    Yields callable actions representing steps in a dialogue script.

    This generator function processes a dialogue graph represented as a parsed
    JSON object.  Each yielded callable performs an action, such as delivering a
    line of dialogue, triggering an event, or prompting user input to determine
    the next branch of the dialogue.

    Args:
        dialogue: A dict representing the parsed dialogue script.
        context: A dict of shared state that persists across the dialogue run.

    Yields:
        A function that performs the next step in the dialogue sequence.
    """
    nodes: dict[str, Generator] = {}

    def callback(name):
        return callbacks.get(name, lambda *_: None)

    def change_node(_):
        return nodes.get(context.pop("next_node", None), None)

    def eval_expr(expr, extra=None):
        return eval(str(expr), context.copy(), extra or {})

    def jump(target=None, condition=None):

        def transition(_, target=target):
            return target if condition is None or eval_expr(condition) else None

        return transition

    def update_context(assignments: dict):
        context.update({k: eval_expr(v) for k, v in assignments.items()})

    def prompt(all_options: list[dict]):
        times_seen: Counter[tuple] = Counter()

        def is_shown(option):
            seen = times_seen[tuple(option.items())]
            return eval_expr(option.get("if", "True"), extra={"_seen": seen})

        def get_options():
            options = [option for option in all_options if is_shown(option)]
            choice = context.pop("choice", None)

            if choice in options:
                context["next_node"] = choice["value"]
                return

            times_seen.update([tuple(option.items()) for option in options])
            callback("prompt")(options)

        return get_options

    def make_action(action_data):
        match action_data:
            case "update_context", dict(assignments):
                return partial(update_context, assignments)
            case "next_node", str(node_name):
                return partial(context.update, next_node=node_name)
            case "pause", float(duration):
                return partial(callback("pause"), duration)
            case "options", list(options):
                return prompt(options)
            case "stage_direction", dict(params):
                return partial(callback("stage_direction"), params)
            case str(actor), str(line):
                return partial(callback("speak"), actor, line)
            case _:
                raise ValueError(f"Invalid action: {action_data}")

    def make_node(name: str, node_data: list[dict]):
        transitions: dict[Action, list[Callable]] = defaultdict(list)
        fork: Action | None = None
        jump_else = jump(None)

        actions = [(_.pop("if", None), make_action(_.popitem())) for _ in node_data]
        actions += [(None, None)]

        # XXX what if the first action has a condition?
        for (_, action), (condition, next_) in pairwise(actions):
            if condition:
                fork = fork or action
                transitions[fork].append(jump(next_, condition))
                if action != fork:
                    transitions[action].append(jump_else)
            else:
                if fork:
                    jump_else.__defaults__ = (next_,)
                    jump_else = jump(None)
                    fork = None
                transitions[action].append(jump(next_, condition))

        nodes[name] = statemachine(transitions)
        return nodes[name], [change_node]

    sm = statemachine(dict(make_node(name, node) for name, node in dialogue.items()))
    node = next(sm)
    input_ = None
    while node:
        action = node.send(input_)
        yield action
        input_ = context
        if "next_node" in context:
            if context["next_node"] == "end":
                break
            node.send(statemachine.RESET)  # type: ignore
            node = sm.send(context)
            input_ = None

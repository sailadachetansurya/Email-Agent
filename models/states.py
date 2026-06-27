from enum import Enum


class TaskState(Enum):
    PENDING = "pending"
    CLASSIFIED = "classified"
    AWAITING_HUMAN = "awaiting_human_response"
    COMPLETED = "completed"
    LOGGED = "logged & completed"
    FAILED = "failed"

    def __str__(self):
        return self.value


VALID_TRANSITIONS = {
    TaskState.PENDING: [TaskState.CLASSIFIED, TaskState.FAILED],
    TaskState.CLASSIFIED: [TaskState.AWAITING_HUMAN, TaskState.COMPLETED, TaskState.FAILED],
    TaskState.AWAITING_HUMAN: [TaskState.COMPLETED, TaskState.FAILED],
    TaskState.COMPLETED: [TaskState.LOGGED, TaskState.FAILED],
    TaskState.LOGGED: [],
    TaskState.FAILED: [TaskState.PENDING],
}


class InvalidTransitionError(Exception):
    pass


def transition(current, target):
    if target not in VALID_TRANSITIONS.get(current, []):
        raise InvalidTransitionError(
            f"Cannot transition from '{current.value}' to '{target.value}'"
        )
    return target

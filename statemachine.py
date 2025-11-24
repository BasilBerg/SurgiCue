from enum import auto, Enum


class States(Enum):
    POINTER = auto()
    DRAW = auto()
    ERASE = auto()
    LINE = auto()
    UNDO = auto()
    CLEAR = auto()
    FAILSAFE = auto()


class ClickType(Enum):
    NONE = auto()
    LEFT_SINGLE = auto()
    LEFT_DOUBLE = auto()
    LEFT_LONG = auto()
    RIGHT_SINGLE = auto()
    RIGHT_DOUBLE = auto()
    RIGHT_LONG = auto()


def transition_states(self):
    try:
        match self.state:
            case States.POINTER:
                match self.latest_click:
                    case ClickType.RIGHT_SINGLE:
                        self.state = States.DRAW
                    case ClickType.RIGHT_DOUBLE:
                        self.state = States.LINE
                    case ClickType.LEFT_SINGLE:
                        self.state = States.ERASE
                    case ClickType.LEFT_DOUBLE:
                        self.state = States.UNDO
                    case ClickType.LEFT_LONG | ClickType.RIGHT_LONG:
                        self.state = States.CLEAR
                    case ClickType.NONE:
                        pass

            case States.DRAW:
                match self.latest_click:
                    case ClickType.RIGHT_SINGLE:
                        self.state = States.POINTER
                    case ClickType.RIGHT_DOUBLE:
                        self.state = States.LINE
                    case ClickType.LEFT_SINGLE:
                        self.state = States.ERASE
                    case ClickType.LEFT_DOUBLE:
                        self.state = States.UNDO
                    case ClickType.LEFT_LONG | ClickType.RIGHT_LONG:
                        self.state = States.CLEAR
                    case ClickType.NONE:
                        pass
            case States.ERASE:
                match self.latest_click:
                    case ClickType.RIGHT_SINGLE:
                        self.state = States.DRAW
                    case ClickType.RIGHT_DOUBLE:
                        self.state = States.LINE
                    case ClickType.LEFT_SINGLE:
                        self.state = States.POINTER
                    case ClickType.LEFT_DOUBLE:
                        self.state = States.UNDO
                    case ClickType.LEFT_LONG | ClickType.RIGHT_LONG:
                        self.state = States.CLEAR
                    case ClickType.NONE:
                        pass
            case States.LINE:
                match self.latest_click:
                    case ClickType.RIGHT_SINGLE:
                        self.state = States.POINTER
                    case ClickType.RIGHT_DOUBLE:
                        self.state = States.LINE
                    case ClickType.LEFT_SINGLE:
                        self.state = States.ERASE
                    case ClickType.LEFT_DOUBLE:
                        self.state = States.UNDO
                    case ClickType.LEFT_LONG | ClickType.RIGHT_LONG:
                        self.state = States.CLEAR
                    case ClickType.NONE:
                        pass
            case States.UNDO:
                pass
            case States.CLEAR:
                pass
            case States.FAILSAFE:
                pass
            case _:
                self.start_failsafe_mode('Unknown State during transition', ValueError('Invalid State'))
                pass
        self.latest_click = ClickType.NONE
    except Exception as e:
        self.start_failsafe_mode('Error during state transition', e)

import os
import tkinter
import time
from enum import Enum, auto

from PIL import Image, ImageTk

FPS = 60

BACKGROUND_COLOR = '#BBBBBB'  # TODO: change to #FFFFFF
COLOR = '#00FF00'
ERASER_COLOR = '#FFFFFF'
LONG_PRESS_DURATION = 0.5
DOUBLE_CLICK_THRESHOLD = 0.2

POINTER_SIZE = 50
UI_LINE_WIDTH = 5
DRAWING_WIDTH = 10
ERASER_WIDTH = 30
LINE_WIDTH = 10

ICON_DIRECTORY = 'icons/'
ICON_SIZE = 100
ICON_TINT = '#FF0000'
ICON_DURATION = 0.5


def get_current_time():
    return time.perf_counter()


class ClickType(Enum):
    NONE = auto()
    LEFT_SINGLE = auto()
    LEFT_DOUBLE = auto()
    LEFT_LONG = auto()
    RIGHT_SINGLE = auto()
    RIGHT_DOUBLE = auto()
    RIGHT_LONG = auto()


class States(Enum):
    POINTER = auto()
    DRAW = auto()
    ERASE = auto()
    LINE = auto()
    UNDO = auto()
    CLEAR = auto()


class SurgiCue:
    def __init__(self):
        self.root = tkinter.Tk()
        self.root.title('SurgiCue')
        self.root.attributes('-fullscreen', True)
        try:
            icon_path = os.path.join(ICON_DIRECTORY, 'window-icon.png')
            self._win_icon = tkinter.PhotoImage(file=icon_path)
            self.root.iconphoto(True, self._win_icon)
        except Exception as e:
            print(f"[WARNING] Icon not found ({icon_path}): {e}")

        self.w = self.root.winfo_screenwidth()
        self.h = self.root.winfo_screenheight()
        self.canvas = tkinter.Canvas(self.root, width=self.w, height=self.h, bg=BACKGROUND_COLOR, highlightthickness=0)
        self.canvas.pack(fill=tkinter.BOTH, expand=True)

        self.last_left_click_time = 0
        self.last_left_release_time = 0
        self.last_right_click_time = 0
        self.last_right_release_time = 0
        self.latest_click = ClickType.NONE
        self.last_click_coordinates = (0, 0)
        self.pointer_coordinates = (0, 0)

        self.drawn_object_ids = []

        self.line_start_coordinates = None
        self.draw_coordinates = []
        self.erase_coordinates = []
        self.current_draw_id = None
        self.current_erase_id = None
        self.line_end_coordinates = None
        self.line_preview_id = None

        self.cleared_objects = []

        self.last_action_icon_time = 0

        self.root.bind('<Escape>', lambda e: self.root.destroy())
        self.canvas.bind('<ButtonPress-1>', self.handle_clicks('left_pressed'))
        self.canvas.bind('<ButtonRelease-1>', self.handle_clicks('left_released'))
        # self.canvas.bind('<Double-Button-1>', self.handle_clicks('left_double'))
        self.canvas.bind('<ButtonPress-3>', self.handle_clicks('right_pressed'))
        self.canvas.bind('<ButtonRelease-3>', self.handle_clicks('right_released'))
        # self.canvas.bind('<Double-Button-3>', self.handle_clicks('right_double'))
        self.canvas.bind('<Motion>', self.handle_motion())

        self.state = States.POINTER

        self.loop()

    def handle_clicks(self, event_type):
        def handler(event):
            x, y = event.x, event.y
            # print(f'Event: {event_type}, X: {x}, Y: {y}')
            current_time = get_current_time()
            print(current_time)

            match event_type:
                case 'left_pressed':

                    self.last_left_click_time = current_time

                case 'left_released':

                    if current_time - self.last_left_release_time < DOUBLE_CLICK_THRESHOLD:
                        self.latest_click = ClickType.LEFT_DOUBLE


                    elif current_time - self.last_left_click_time < LONG_PRESS_DURATION:
                        self.last_left_release_time = current_time
                        self.latest_click = ClickType.LEFT_SINGLE

                    else:
                        self.latest_click = ClickType.LEFT_LONG

                # case 'left_double':
                #     print('Double Left Click detected')
                #     self.last_click = ClickType.LEFT_DOUBLE

                case 'right_pressed':
                    self.last_right_click_time = current_time

                case 'right_released':

                    if current_time - self.last_right_release_time < DOUBLE_CLICK_THRESHOLD:
                        self.latest_click = ClickType.RIGHT_DOUBLE

                    elif current_time - self.last_right_click_time < LONG_PRESS_DURATION:
                        self.latest_click = ClickType.RIGHT_SINGLE
                        self.last_right_release_time = current_time

                    else:
                        self.latest_click = ClickType.RIGHT_LONG

                # case 'right_double':
                #     self.last_click = ClickType.RIGHT_DOUBLE
                #     print('Double Right Click detected')

            self.last_click_coordinates = (x, y)
            self.transition_states()

        return handler

    def handle_motion(self):
        def handler(event):
            self.pointer_coordinates = (event.x, event.y)

        return handler

    def transition_states(self):
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
            case _:
                pass
                # TODO:throw error
        self.latest_click = ClickType.NONE

    def perform_state_actions(self):
        self.canvas.delete('overlay')

        icon_filename = ''
        x, y = self.pointer_coordinates

        if (self.line_end_coordinates != None):
            # draw line
            self.line_end_coordinates = None

        match self.state:
            case States.POINTER:
                # icon_filename = 'pointer.png'
                half = POINTER_SIZE // 2
                self.canvas.create_line(x - half, y, x + half, y, fill=COLOR, width=UI_LINE_WIDTH,
                                        tags=('overlay', 'pointer'))
                self.canvas.create_line(x, y - half, x, y + half, fill=COLOR, width=UI_LINE_WIDTH,
                                        tags=('overlay', 'pointer'))

            case States.DRAW:
                icon_filename = 'draw.png'
                self.draw_rectangle(COLOR, COLOR, DRAWING_WIDTH, UI_LINE_WIDTH, x, y)
                self.draw(x, y)

            case States.ERASE:
                icon_filename = 'erase.png'
                self.draw_rectangle(ERASER_COLOR, COLOR, ERASER_WIDTH, UI_LINE_WIDTH, x, y)
                self.erase(x, y)

            case States.LINE:
                icon_filename = 'line.png'
                self.draw_rectangle(COLOR, COLOR, DRAWING_WIDTH, UI_LINE_WIDTH, x, y)

                if self.line_start_coordinates is None:
                    self.line_start_coordinates = (x, y)
                start_x, start_y = self.line_start_coordinates

                self.canvas.create_line(start_x, start_y, x, y, fill=COLOR, width=LINE_WIDTH,
                                        tags=('overlay', 'line_preview'))

            case States.UNDO:
                self.last_action_icon_time = get_current_time()
                icon_filename = 'undo.png'

                self.undo()

                self.state = States.POINTER

            case States.CLEAR:
                self.last_action_icon_time = get_current_time()
                icon_filename = 'clear.png'
                self.clear_canvas()
                self.state = States.POINTER

            case _:
                pass

        # finish line
        if self.state != States.LINE and self.line_start_coordinates is not None:
            start_x, start_y = self.line_start_coordinates
            end_x, end_y = self.pointer_coordinates
            if (start_x, start_y) != (end_x, end_y):
                object_id = self.canvas.create_line(start_x, start_y, end_x, end_y, fill=COLOR, width=LINE_WIDTH,
                                                    tags=('drawn',))
                self.drawn_object_ids.append(object_id)
            self.line_start_coordinates = None

        if self.state != States.DRAW and (self.current_draw_id is not None or len(self.draw_coordinates) == 1):
            if (self.current_draw_id is not None):
                self.drawn_object_ids.append(self.current_draw_id)
            self.draw_coordinates = []
            self.current_draw_id = None

        if self.state != States.ERASE and (self.current_erase_id is not None or len(self.erase_coordinates) == 1):
            if (self.current_erase_id is not None):
                self.drawn_object_ids.append(self.current_erase_id)
            self.erase_coordinates = []
            self.current_erase_id = None

        self.display_icon(icon_filename)

    def draw(self, x: int, y: int):
        coordinates_length = len(self.draw_coordinates)
        if coordinates_length > 0:
            previous_x, previous_y = self.draw_coordinates[-1]
            if (round(previous_x), round(previous_y)) == (round(x), round(y)):
                return

            if coordinates_length == 1:
                self.current_draw_id = self.canvas.create_line(
                    previous_x, previous_y, x, y,
                    fill=COLOR,
                    width=DRAWING_WIDTH,
                    smooth=True,
                    capstyle='round',
                    tags=('drawn')
                )
            else:
                self.canvas.coords(
                    self.current_draw_id,
                    *self.canvas.coords(self.current_draw_id),
                    x, y
                )
        self.draw_coordinates.append((x, y))

    def erase(self, x: int, y: int):
        coordinates_length = len(self.erase_coordinates)
        if coordinates_length > 0:
            previous_x, previous_y = self.erase_coordinates[-1]
            if (round(previous_x), round(previous_y)) == (round(x), round(y)):
                return

            if coordinates_length == 1:
                self.current_erase_id = self.canvas.create_line(
                    previous_x, previous_y, x, y,
                    fill=ERASER_COLOR,
                    width=ERASER_WIDTH,
                    smooth=True,
                    capstyle='round',
                    tags=('drawn')
                )
            else:
                self.canvas.coords(
                    self.current_erase_id,
                    *self.canvas.coords(self.current_erase_id),
                    x, y
                )
        self.erase_coordinates.append((x, y))

    def undo(self):
        if len(self.drawn_object_ids) > 0:
            object_to_delete = self.drawn_object_ids.pop()
            self.canvas.delete(object_to_delete)
        elif len(self.cleared_objects) > 0:
            for cleared_object in self.cleared_objects:
                coords, options = cleared_object
                options_extracted = {key: val[-1] for key, val in options.items()}
                new_id = self.canvas.create_line(*coords, **options_extracted)
                self.drawn_object_ids.append(new_id)
            self.cleared_objects.clear()





    def clear_canvas(self):
        self.cleared_objects.clear()
        for object_id in self.drawn_object_ids:
            coords = self.canvas.coords(object_id)
            options = self.canvas.itemconfig(object_id)
            self.cleared_objects.append((coords, options))
            self.canvas.delete(object_id)
        self.drawn_object_ids.clear()

    def draw_rectangle(self, color: str, outline_color: str, line_width: int, border_width: int, x: int, y: int):
        half = line_width // 2
        self.canvas.create_rectangle(x - half, y - half, x + half, y + half,
                                     fill=color, outline=outline_color, width=border_width,
                                     tags=('overlay', 'pointer'))

    def loop(self):
        self.perform_state_actions()
        self.root.after(1000 // FPS, self.loop)

    def run(self):
        self.root.mainloop()

    def display_icon(self, filename: str):
        if (filename == ''):
            if (get_current_time() - self.last_action_icon_time > ICON_DURATION):
                self.canvas.delete('icon')
                self.last_action_icon_time = 0
            return

        icon_position = (10, 10)

        try:
            icon_path = os.path.join(ICON_DIRECTORY, filename)
            icon = Image.open(icon_path).convert("RGBA")
            resized_icon = icon.resize((ICON_SIZE, ICON_SIZE))
            alpha_channel = resized_icon.getchannel('A')
            tinted_icon = Image.new("RGBA", resized_icon.size, ICON_TINT)
            tinted_icon.putalpha(alpha_channel)
            self.icon_image = ImageTk.PhotoImage(tinted_icon)
            self.canvas.create_image(icon_position, anchor="nw", image=self.icon_image, tags=('icon'))

        except Exception as e:
            print(f"[WARNING] Icon not found ({icon_path}): {e}")
            toolname = filename.split(".")[0]
            self.canvas.create_text(icon_position, anchor="nw", text=toolname, fill=ICON_TINT,
                                    font=("Arial", ICON_SIZE // 5, "bold"), tags=('icon'))


if __name__ == '__main__':
    SurgiCue().run()

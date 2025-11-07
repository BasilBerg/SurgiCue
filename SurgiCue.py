import os
import tkinter
import time
from enum import Enum, auto
from PIL import Image, ImageTk
import logging

logging.basicConfig(
    level=logging.INFO,
    filename="SurgiCue.log",
    format="{asctime} - {levelname} - {message}",
    style="{"
)

FPS = 60

BACKGROUND_COLOR = '#FFFFFF'
DRAWING_COLOR = '#00FF00'
ERASER_COLOR = BACKGROUND_COLOR
LONG_PRESS_DURATION = 0.5
DOUBLE_CLICK_THRESHOLD = 0.2

POINTER_SIZE = 50
UI_LINE_WIDTH = POINTER_SIZE/10
DRAWING_WIDTH = POINTER_SIZE/5
ERASER_WIDTH = POINTER_SIZE*2
LINE_WIDTH = DRAWING_WIDTH

ICON_DIRECTORY = 'icons/'
ICON_SIZE = 150
ICON_TINT = DRAWING_COLOR
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
    FAILSAFE = auto()


class SurgiCue:
    def __init__(self):
        self.root = tkinter.Tk()
        self.root.title('SurgiCue')
        self.root.attributes('-fullscreen', True)
        self.root.config(cursor="none")
        icon_path = os.path.join(ICON_DIRECTORY, 'window-icon.png')
        try:
            self._win_icon = tkinter.PhotoImage(file=icon_path)
            self.root.iconphoto(True, self._win_icon)
        except Exception as e:
            logging.warning(f"Window Icon could not be set. ({icon_path}): {e}")

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.canvas = tkinter.Canvas(self.root, width=self.screen_width, height=self.screen_height, bg=BACKGROUND_COLOR,
                                     highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        self.root.bind('<Escape>', lambda event: self.root.destroy())
        self.canvas.bind('<ButtonPress-1>', self.handle_clicks('left_pressed'))
        self.canvas.bind('<ButtonRelease-1>', self.handle_clicks('left_released'))
        self.canvas.bind('<ButtonPress-3>', self.handle_clicks('right_pressed'))
        self.canvas.bind('<ButtonRelease-3>', self.handle_clicks('right_released'))
        self.canvas.bind('<Motion>', self.handle_motion())

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
        self.current_line_id = None

        self.cleared_objects = []

        self.last_action_icon_time = 0
        self.icon_cache = {}

        self.state = States.POINTER
        self.failsafe_mode = False

        self.loop()

    def handle_clicks(self, event_type):
        def handler(event):
            x, y = event.x, event.y
            current_time = get_current_time()
            try:
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

                    case 'right_pressed':
                        self.last_right_click_time = current_time

                    case 'right_released':

                        if current_time - self.last_right_release_time < DOUBLE_CLICK_THRESHOLD:
                            self.latest_click = ClickType.RIGHT_DOUBLE

                        elif current_time - self.last_right_click_time < LONG_PRESS_DURATION:
                            self.last_right_release_time = current_time
                            self.latest_click = ClickType.RIGHT_SINGLE

                        else:
                            self.latest_click = ClickType.RIGHT_LONG

                self.last_click_coordinates = (x, y)
                self.transition_states()

            except Exception as e:
                self.start_failsafe_mode('Error handling click event', e)

        return handler

    def handle_motion(self):
        def handler(event):
            self.pointer_coordinates = (event.x, event.y)

        return handler

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

    def start_failsafe_mode(self, message: str, exception: Exception):
        logging.critical('Entering failsafe mode due to error: %s', message)
        logging.exception(exception)
        self.canvas.delete('all')
        self.failsafe_mode = True
        try:
            self.canvas.create_text(10, 10, anchor="nw", text='FAILSAFE MODE', fill=ICON_TINT,
                                    font=("Arial", ICON_SIZE // 5, "bold"), tags='icon')
            self.canvas.unbind('<ButtonPress-1>')
            self.canvas.unbind('<ButtonRelease-1>')
            self.canvas.unbind('<ButtonPress-3>')
            self.canvas.unbind('<ButtonRelease-3>')
            self.canvas.unbind('<Motion>')
        except Exception as e:
            logging.exception('Error while starting failsafe mode: %s', e)

    def perform_state_actions(self):
        try:
            self.canvas.delete('overlay')

            icon_filename = ''
            pointer_x, pointer_y = self.pointer_coordinates

            match self.state:
                case States.POINTER:
                    self.display_crosshair(pointer_x, pointer_y)
                case States.DRAW:
                    icon_filename = 'draw.png'
                    self.display_tool_preview(DRAWING_COLOR, DRAWING_COLOR, DRAWING_WIDTH, UI_LINE_WIDTH, pointer_x, pointer_y)
                    self.draw(pointer_x, pointer_y)

                case States.ERASE:
                    icon_filename = 'erase.png'
                    self.display_tool_preview(ERASER_COLOR, DRAWING_COLOR, ERASER_WIDTH, UI_LINE_WIDTH, pointer_x, pointer_y)
                    self.erase(pointer_x, pointer_y)

                case States.LINE:
                    icon_filename = 'line.png'
                    self.display_tool_preview(DRAWING_COLOR, DRAWING_COLOR, DRAWING_WIDTH, UI_LINE_WIDTH, pointer_x, pointer_y)
                    self.draw_line(pointer_x, pointer_y)

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

                case States.FAILSAFE:
                    pass
                case _:
                    self.start_failsafe_mode('Unknown State during action performance', Exception('Invalid State'))
                    pass

            # finish drawing
            if self.state != States.DRAW and (self.current_draw_id is not None or len(self.draw_coordinates) == 1):
                if self.current_draw_id is not None:
                    self.drawn_object_ids.append(self.current_draw_id)
                self.draw_coordinates = []
                self.current_draw_id = None

            # finish line
            if self.state != States.LINE and self.current_line_id is not None:
                self.drawn_object_ids.append(self.current_line_id)
                self.current_line_id = None
                self.line_start_coordinates = None

            # finish erasing
            if self.state != States.ERASE and (self.current_erase_id is not None or len(self.erase_coordinates) == 1):
                if self.current_erase_id is not None:
                    self.drawn_object_ids.append(self.current_erase_id)
                self.erase_coordinates = []
                self.current_erase_id = None

            self.display_icon(icon_filename)
        except Exception as e:
            self.start_failsafe_mode('Error performing state actions', e)

    def draw(self, x: int, y: int):
        try:
            coordinates_length = len(self.draw_coordinates)
            if coordinates_length > 0:
                previous_x, previous_y = self.draw_coordinates[-1]
                if (previous_x, previous_y) == (x, y):
                    return

                if coordinates_length == 1:
                    self.current_draw_id = self.canvas.create_line(
                        previous_x, previous_y, x, y,
                        fill=DRAWING_COLOR,
                        width=DRAWING_WIDTH,
                        tags='drawn'
                    )
                else:
                    self.canvas.coords(
                        self.current_draw_id,
                        *self.canvas.coords(self.current_draw_id),
                        x, y
                    )
            self.draw_coordinates.append((x, y))
        except Exception as e:
            self.start_failsafe_mode('Error during drawing', e)

    def draw_line(self, x, y):
        try:
            if self.line_start_coordinates is None:
                self.line_start_coordinates = (x, y)
            start_x, start_y = self.line_start_coordinates

            if self.current_line_id is None:
                self.current_line_id = self.canvas.create_line(start_x, start_y, x, y, fill=DRAWING_COLOR, width=LINE_WIDTH,
                                                               capstyle='round', tags='drawn')
            else:
                self.canvas.coords(self.current_line_id, start_x, start_y, x, y)
        except Exception as e:
            self.start_failsafe_mode('Error during line drawing', e)

    def erase(self, x: int, y: int):
        try:
            coordinates_length = len(self.erase_coordinates)
            if coordinates_length > 0:
                previous_x, previous_y = self.erase_coordinates[-1]
                if (previous_x, previous_y) == (x, y):
                    return

                if coordinates_length == 1:
                    self.current_erase_id = self.canvas.create_line(
                        previous_x, previous_y, x, y,
                        fill=ERASER_COLOR,
                        width=ERASER_WIDTH,
                        tags='drawn'
                    )
                else:
                    self.canvas.coords(
                        self.current_erase_id,
                        *self.canvas.coords(self.current_erase_id),
                        x, y
                    )
            self.erase_coordinates.append((x, y))
        except Exception as e:
            self.start_failsafe_mode('Error during erasing', e)

    def undo(self):
        try:
            if len(self.drawn_object_ids) > 0:
                object_to_delete = self.drawn_object_ids.pop()
                self.canvas.delete(object_to_delete)
            elif len(self.cleared_objects) > 0:
                for cleared_object in self.cleared_objects:
                    coordinates, options = cleared_object
                    options_extracted = {key: val[-1] for key, val in options.items()}
                    new_id = self.canvas.create_line(*coordinates, **options_extracted)
                    self.drawn_object_ids.append(new_id)
                self.cleared_objects.clear()
        except Exception as e:
            self.start_failsafe_mode('Error during undo', e)

    def clear_canvas(self):
        try:
            self.cleared_objects.clear()
            for object_id in self.drawn_object_ids:
                coordinates = self.canvas.coords(object_id)
                options = self.canvas.itemconfig(object_id)
                self.cleared_objects.append((coordinates, options))
                self.canvas.delete(object_id)
            self.drawn_object_ids.clear()
        except Exception as e:
            self.start_failsafe_mode('Error during canvas clearing', e)

    def display_tool_preview(self, color: str, outline_color: str, line_width: int, border_width: int, x: int, y: int):
        try:
            half = line_width // 2
            self.canvas.create_rectangle(x - half, y - half, x + half, y + half,
                                         fill=color, outline=outline_color, width=border_width,
                                         tags=('overlay', 'pointer'))
        except Exception as e:
            self.start_failsafe_mode('Error drawing tool preview', e)

    def display_crosshair(self, x: int, y: int):
        try:
            half = POINTER_SIZE // 2
            self.canvas.create_line(x - half, y, x + half, y, fill=DRAWING_COLOR, width=UI_LINE_WIDTH,
                                    tags=('overlay', 'pointer'))
            self.canvas.create_line(x, y - half, x, y + half, fill=DRAWING_COLOR, width=UI_LINE_WIDTH,
                                    tags=('overlay', 'pointer'))
        except Exception as e:
            self.start_failsafe_mode('Error drawing crosshair', e)

    def display_icon(self, filename: str):
        try:
            icon_position = (10, 10)
            if get_current_time() - self.last_action_icon_time >= ICON_DURATION:
                self.canvas.delete('icon')
                self.last_action_icon_time = 0

            if filename == '':
                return
            try:
                icon = self.load_icon(filename)
                self.canvas.delete('icon')
                self.canvas.create_image(icon_position, anchor="nw", image=icon, tags='icon')

            except Exception as e:
                logging.warning(f'Error loading Icon ({filename}), using text as fallback. {e}')

                tool_name = filename.split(".")[0]
                self.canvas.delete('icon')
                self.canvas.create_text(icon_position, anchor="nw", text=tool_name, fill=ICON_TINT,
                                        font=("Arial", ICON_SIZE // 5, "bold"), tags='icon')

        except Exception as e:
            self.start_failsafe_mode('Error displaying icon', e)

    def load_icon(self, filename):
        if filename in self.icon_cache:
            return self.icon_cache[filename]

        icon_path = os.path.join(ICON_DIRECTORY, filename)
        icon = Image.open(icon_path).convert("RGBA")
        resized_icon = icon.resize((ICON_SIZE, ICON_SIZE))
        alpha_channel = resized_icon.getchannel('A')
        tinted_icon = Image.new("RGBA", resized_icon.size, ICON_TINT)
        tinted_icon.putalpha(alpha_channel)

        photo_image = ImageTk.PhotoImage(tinted_icon)
        self.icon_cache[filename] = photo_image
        return photo_image

    def loop(self):
        if not self.failsafe_mode:
            self.perform_state_actions()
            self.root.after(1000 // FPS, self.loop)

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    SurgiCue().run()

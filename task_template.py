import os
import pyxid2
from psychopy import visual, gui, data, event, core
from psychopy.visual.shape import BaseShapeStim
import time
from screeninfo import get_monitors
from PIL import Image


class TaskTemplate:
    """
    A cognitive task template, to use to code cognitive tasks more simply
    """
    bg = "black"
    """Set window background. Default value is black."""
    text_color = "white"
    """Set text color from create_visual_text method. Default value is white."""
    yes_key_code = "o"
    """Set code for "yes" key. Default value is "o"."""
    yes_key_name = "bleue"
    """Set name for "yes" key. Default value is "bleue" (blue in french)."""
    no_key_code = "n"
    """Set code for "no" key. Default value is "n". """
    no_key_name = "verte"
    """Set name for "no" key. Default value is "verte" (green in french)."""
    quit_code = "q"
    """A backdoor to escape task """
    keys = [yes_key_code, no_key_code, "q"]
    """The keys to watch in get_response method."""
    trials = 10
    """Number of trials by user."""
    nb_ans = 2
    "Whether your task is a True/False or a Yes/No paradigm or not"
    launch_example = False
    """Whether your task should show an example. If True, you should overwrite the example method. Can be overwritten 
    at init"""
    response_pad = True
    "Where your task uses a Cedrus Response Pad or not. Put False if not."
    dev = None
    "Cedrus ResponsePad RB-740"
    welcome = "Bienvenue !"
    """Welcome text shown when the task is started."""
    instructions = []
    """instructions on the task given to the user. Should be overwritten as it is empty in template."""
    font_size_instr = 0.06
    """Text size of the instructions"""
    next = f"Pour passer à l'instruction suivante, appuyez sur la touche {yes_key_name}"
    """text to show between 2 screens of instructions."""
    good_luck = "Bonne chance !"
    """Good luck text to show right before first trial"""
    end = "La tâche cognitive est à présent terminée. Merci, et au revoir !"
    """Text to show when all trials are done, and before the end."""
    csv_headers = []
    """Headers of CSV file. Should be overwritten as it is empty in this template."""

    def __init__(self, csv_folder, launch_example=None):
        """
        :param launch_example: Can overwrite default <self.example> value.
        """
        self.right_key_code = None
        self.right_key_name = None
        self.mid_right_key_code = None
        self.mid_right_key_name = None
        self.mid_left_key_code = None
        self.left_key_name = None
        self.left_key_code = None
        self.mid_left_key_name = None

        self.win = visual.Window(
            size=[get_monitors()[0].width, get_monitors()[0].height],
            # if needed, change the size in concordance with your monitor
            fullscr=False,
            units="pix",
            screen=0,
            allowStencil=False,
            monitor='testMonitor',
            color=self.bg,
            colorSpace='rgb'
        )
        exp_info = {'participant': '', "date": data.getDateStr()}
        gui.DlgFromDict(exp_info, title='Subliminal Priming Task', fixed=["date"])
        self.participant = exp_info["participant"]
        file_name = exp_info['participant'] + '_' + exp_info['date'][:-7]
        self.dataFile = open(f"{csv_folder}/{file_name}.csv", 'w')
        self.dataFile.write(", ".join(self.csv_headers))
        self.dataFile.write("\n")
        if launch_example is not None:
            self.launch_example = launch_example
        self.init()

    def init(self):
        """Function launched at the end of constructor if you want to create instance variables or execute some code
        at initialization"""
        if self.response_pad:
            # get the device and save it
            devices = pyxid2.get_xid_devices()
            self.dev = devices[0]
            self.dev.enable_usb_output('K', True)
            print(self.dev)
            if self.nb_ans == 2:
                self.yes_key_name = "verte"
                self.yes_key_code = "6"
                self.no_key_name = "rouge"
                self.no_key_code = "0"
                self.quit_code = "3"
                self.keys = [self.yes_key_code, self.no_key_code, self.quit_code]
            elif self.nb_ans == 4:
                self.left_key_name = "a"
                self.left_key_code = "0"
                self.mid_left_key_name = "z"
                self.mid_left_key_code = "1"
                self.mid_right_key_name = "o"
                self.mid_right_key_code = "5"
                self.right_key_name = "p"
                self.right_key_code = "6"
                self.quit_code = "3"
                self.yes_key_code = "6"
                self.keys = [self.left_key_code, self.mid_left_key_code, self.right_key_code, self.mid_right_key_code,
                             self.yes_key_code, self.quit_code]
        else:
            if self.nb_ans == 2:
                self.yes_key_name = "p"
                self.yes_key_code = "p"
                self.no_key_name = "a"
                self.no_key_code = "a"
                self.quit_code = "q"
                self.keys = [self.yes_key_code, self.no_key_code, self.quit_code]
            elif self.nb_ans == 4:
                print("IN !")
                self.left_key_name = "a"
                self.left_key_code = "a"
                self.mid_left_key_name = "z"
                self.mid_left_key_code = "z"
                self.mid_right_key_name = "o"
                self.mid_right_key_code = "o"
                self.right_key_name = "p"
                self.right_key_code = "p"
                self.quit_code = "q"
                self.yes_key_code = "p"
                self.yes_key_name = "p"
                self.keys = [self.left_key_code, self.mid_left_key_code, self.right_key_code, self.mid_right_key_code,
                             self.quit_code]
                print(self.keys)

    def update_csv(self, *args):
        args = list(map(str, args))
        self.dataFile.write(", ".join(args))
        self.dataFile.write("\n")

    def size(self, img):
        image = Image.open(f'img/{img}')
        imgwidth, imgheight = image.size
        while imgwidth > get_monitors()[0].width:
            imgwidth = imgwidth * 0.9
            imgheight = imgheight * 0.9
        while imgheight > get_monitors()[0].height:
            imgwidth = imgwidth * 0.9
            imgheight = imgheight * 0.9

        return imgwidth, imgheight

    def get_images(self, no_trial):
        return [filename for filename in os.listdir('../img')]

    def get_good_ans(self, answer, dic_values):
        for key, value in dic_values.items():
            if answer == key:
                return value

    def create_visual_text(self, text, pos=(0, 0), font_size=0.06, color="white", units='height'):
        """
        Create a <visual.TextStim> with some default parameters so it's simpler to create visual texts
        """
        return visual.TextStim(
            win=self.win,
            text=text,
            font='Arial',
            units=units,
            pos=pos,
            height=font_size,
            wrapWidth=None,
            ori=0,
            color=color,
            colorSpace='rgb',
            opacity=1,
            languageStyle='LTR',
        )

    def create_visual_image(self, image, size, pos=(0, 0), ori=0.0, units='pix'):
        return visual.ImageStim(
            win=self.win,
            image=image,
            size=size,
            pos=pos,
            ori=ori,
            units=units)

    def create_visual_rect(self, color):
        return visual.Rect(
            win=self.win,
            width=300,
            height=100,
            lineColor=color,
            fillColor=color,
        )

    def create_visual_circle(self, color, pos):
        return visual.Circle(
            win=self.win,
            radius=30,
            fillColor=color,
            lineWidth=0,
            pos=pos,
        )

    def check_break(self, no_trial, first_threshold, second_threshold=None, test=False):
        if no_trial == first_threshold:
            self.create_visual_text("10 minutes de pause").draw()
            self.win.flip()
            if not test:
                core.wait(540)
            else:
                core.wait(10)
            self.create_visual_text("Plus qu'une minute !").draw()
            self.win.flip()
            if not test:
                core.wait(60)
            else:
                core.wait(10)

        elif second_threshold is not None and no_trial == second_threshold:
            self.create_visual_text("5 minutes de pause").draw()
            self.win.flip()
            if not test:
                core.wait(540)
            else:
                core.wait(10)
            self.create_visual_text("Plus qu'une minute !").draw()
            self.win.flip()
            if not test:
                core.wait(60)
            else:
                core.wait(10)

    def wait_yes(self, response_pad):
        """wait until user presses <self.yes_key_code>
        """
        while self.get_response(self.response_pad) != self.yes_key_code:
            pass


    def quit_experiment(self):
        """Ends the experiment
        """
        self.dataFile.close()
        exit()

    def get_response(self, response_pad, keys=None, timeout=float("inf")):
        """Waits for a response from the participant.
        Pressing Q while the function is wait for a response will quit the experiment.
        Returns the pressed key.
        """

        if keys is None:
            keys = self.keys

        if response_pad:
            self.dev.clear_response_queue()
            while not self.dev.has_response():
                self.dev.poll_for_response()
            resp = self.dev.get_next_response()
            print("resp", resp)
            self.dev.clear_response_queue()
            if str(resp["key"]) == self.quit_code:
                self.quit_experiment()
            return str(resp["key"])
        else:
            resp = event.waitKeys(keyList=keys, clearEvents=True, maxWait=timeout)
            if resp is None:
                return
            if resp[0] == self.quit_code:
                self.quit_experiment()
            return resp[0]

    def get_response_with_time(self, response_pad, keys=None, timeout=float("inf")):
        """Waits for a response from the participant.
                Pressing Q while the function is wait for a response will quit the experiment.
                Returns the pressed key and time (in seconds) since the method has been launched.
                """
        if keys is None:
            keys = self.keys
        if response_pad:
            self.dev.clear_response_queue()
            while not self.dev.has_response():
                self.dev.poll_for_response()
            resp = self.dev.get_next_response()
            print("resp : ", resp)
            self.dev.clear_response_queue()
            if str(resp["key"]) == self.quit_code:
                self.quit_experiment()
            return str(resp["key"]), resp["time"] / 1000
        else:
            clock = core.Clock()
            resp = event.waitKeys(timeout, keys, timeStamped=clock)
            if resp is None:
                return resp
            if resp[0][0] == self.quit_code:
                self.quit_experiment()
            return resp[0]

    def task(self, no_trial, exp_start_timestamp, trial_start_timestamp):
        """Method to overwrite to implement your cognitive task.
        :param trial_start_timestamp: Timestamp got right before this trial
        :param exp_start_timestamp: Timestamp got right before first trial
        :param no_trial: Trial number (starting from 0).
        """

    def example(self, exp_start_timestamp):
        """Method to overwrite to implement an example in your cognitive task. Will be launch only if
        <self.launch_example> is True.
        """

    def start(self):
        exp_start_timestamp = time.time()
        self.win.winHandle.set_fullscreen(True)
        self.win.flip()
        self.win.mouseVisible = False
        self.create_visual_text(self.welcome).draw()
        self.win.flip()
        core.wait(2)
        next = self.create_visual_text(self.next, (0, -0.4), 0.04)
        for instr in self.instructions:
            self.create_visual_text(instr, font_size=self.font_size_instr).draw()
            next.draw()
            self.win.flip()
            self.wait_yes(self.response_pad)
        if self.launch_example:
            self.example(exp_start_timestamp)
        self.create_visual_text(self.good_luck).draw()
        self.win.flip()
        core.wait(2)
        for i in range(self.trials):
            trial_start_timestamp = time.time()
            self.task(i, exp_start_timestamp, trial_start_timestamp)
        self.create_visual_text(self.end).draw()
        self.win.flip()
        core.wait(60)
        self.dataFile.close()
        self.quit_experiment()

import os
import sys

import pyxid2
import tobii_research
from psychopy import visual, gui, data, event, core
from psychopy.visual.shape import BaseShapeStim
import tobii_research as tr
import time
from screeninfo import get_monitors
from PIL import Image, ImageDraw
from psychopy.tools.monitorunittools import deg2cm, deg2pix, pix2cm, cm2pix
from psychopy import monitors
import numpy as np
import types
import datetime
import time
import warnings


def cm2deg(cm, monitor, correctFlat=False):
    """
    Bug-fixed version of psychopy.tools.monitorunittools.cm2deg
    (PsychoPy version<=1.85.1).
    """

    if not isinstance(monitor, monitors.Monitor):
        msg = ("cm2deg requires a monitors.Monitor object as the second "
               "argument but received %s")
        raise ValueError(msg % str(type(monitor)))
    dist = monitor.getDistance()
    if dist is None:
        msg = "Monitor %s has no known distance (SEE MONITOR CENTER)"
        raise ValueError(msg % monitor.name)
    if correctFlat:
        return np.degrees(np.arctan(cm / dist))
    else:
        return cm / (dist * 0.017455)


def pix2deg(pixels, monitor, correctFlat=False):
    """
    Bug-fixed version of psychopy.tools.monitorunittools.pix2deg
    (PsychoPy version<=1.85.1).
    """

    scrWidthCm = monitor.getWidth()
    scrSizePix = monitor.getSizePix()
    if scrSizePix is None:
        msg = "Monitor %s has no known size in pixels (SEE MONITOR CENTER)"
        raise ValueError(msg % monitor.name)
    if scrWidthCm is None:
        msg = "Monitor %s has no known width in cm (SEE MONITOR CENTER)"
        raise ValueError(msg % monitor.name)
    cmSize = pixels * float(scrWidthCm) / scrSizePix[0]
    return cm2deg(cmSize, monitor, correctFlat)


default_calibration_target_dot_size = {
    'pix': 2.0, 'norm': 0.004, 'height': 0.002, 'cm': 0.05,
    'deg': 0.05, 'degFlat': 0.05, 'degFlatPos': 0.05
}
default_calibration_target_disc_size = {
    'pix': 2.0 * 20, 'norm': 0.004 * 20, 'height': 0.002 * 20, 'cm': 0.05 * 20,
    'deg': 0.05 * 20, 'degFlat': 0.05 * 20, 'degFlatPos': 0.05 * 20
}

default_key_index_dict = {
    '1': 0, 'num_1': 0, '2': 1, 'num_2': 1, '3': 2, 'num_3': 2,
    '4': 3, 'num_4': 3, '5': 4, 'num_5': 4, '6': 5, 'num_6': 5,
    '7': 6, 'num_7': 6, '8': 7, 'num_8': 7, '9': 8, 'num_9': 8
}


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
    flag_code = "f"
    """Flag to determine beginning of the task on the EEG. Default value is "f"""
    flag_name = "de couleur violette au centre"
    """Set name for "flag" key. Default value is "pastille mauve centrale"""
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
    flag = f"Pour débuter l'expérience, appuyez sur la touche {flag_name}"
    """text to show at the beginning of the task"""
    good_luck = "Bonne chance !"
    """Good luck text to show right before first trial"""
    end = "L'expérience est à présent terminée.\n\n Veuillez appeler l'examinateur. \n\n Merci, et au revoir !"
    """Text to show when all trials are done, and before the end."""
    csv_headers = []
    """Headers of CSV file. Should be overwritten as it is empty in this template."""
    exp_start_timestamp = time.time()
    "Determine the absolute timestamp of the task"
    response_pad_timestamp = 0
    "Time stamp since the RP has been plugged"

    ### EYE TRACKER VARIABLES
    eyetracker = None
    calibration = None
    gaze_data = []
    event_data = []
    retry_points = []
    datafile = None
    embed_events = False
    recording = False
    key_index_dict = default_key_index_dict.copy()

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
            units="height",
            screen=0,
            allowStencil=False,
            monitor='testMonitor',
            color=self.bg,
            colorSpace='rgb'
        )
        exp_info = {'participant': '', "date": data.getDateStr()}
        gui.DlgFromDict(exp_info, title='Psychopy Task', fixed=["date"])
        self.participant = exp_info["participant"]
        self.file_name = exp_info['participant'] + '_' + exp_info['date'][:-7]
        self.dataFile = open(f"{csv_folder}/{self.file_name}.csv", 'w')
        self.dataFile.write(",".join(self.csv_headers))
        self.dataFile.write("\n")
        if launch_example is not None:
            self.launch_example = launch_example

        self.calibration_target_dot_size = default_calibration_target_dot_size[self.win.units]
        self.calibration_target_disc_size = default_calibration_target_disc_size[self.win.units]
        self.calibration_target_dot = visual.Circle(self.win,
                                                    radius=self.calibration_target_dot_size, fillColor='white',
                                                    lineColor=None, lineWidth=1, autoLog=False)
        self.calibration_target_disc = visual.Circle(self.win,
                                                     radius=self.calibration_target_disc_size,
                                                     fillColor='red',
                                                     lineColor='red', lineWidth=1, autoLog=False)

        self.update_calibration = self.update_calibration_default
        if self.win.units == 'norm':  # fix oval
            self.calibration_target_dot.setSize([float(self.win.size[1]) / self.win.size[0], 1.0])
            self.calibration_target_disc.setSize([float(self.win.size[1]) / self.win.size[0], 1.0])

        self.init()

    def init(self):
        """Function launched at the end of constructor if you want to create instance variables or execute some code
        at initialization"""
        if self.response_pad:
            # get the device and save it
            devices = pyxid2.get_xid_devices()
            self.dev = devices[0]
            self.dev.enable_usb_output('K', True)
            self.response_pad_timestamp = time.time()
            print(self.dev)
            if self.nb_ans == 2:
                self.yes_key_name = "verte"
                self.yes_key_code = "6"
                self.no_key_name = "rouge"
                self.no_key_code = "0"
                self.quit_code = "4"
                self.flag_code = "3"
                self.keys = [self.yes_key_code, self.no_key_code, self.flag_code, self.quit_code]
            elif self.nb_ans == 4:
                self.left_key_name = "a"
                self.left_key_code = "0"
                self.mid_left_key_name = "z"
                self.mid_left_key_code = "1"
                self.mid_right_key_name = "o"
                self.mid_right_key_code = "5"
                self.right_key_name = "p"
                self.right_key_code = "6"
                self.flag_code = "3"
                self.quit_code = "4"
                self.yes_key_code = "6"
                self.keys = [self.left_key_code, self.mid_left_key_code, self.right_key_code, self.mid_right_key_code,
                             self.yes_key_code, self.flag_code, self.quit_code]
        else:
            if self.nb_ans == 2:
                self.yes_key_name = "p"
                self.yes_key_code = "p"
                self.no_key_name = "a"
                self.no_key_code = "a"
                self.flag_code = "f"
                self.quit_code = "q"
                self.keys = [self.yes_key_code, self.no_key_code, self.flag_code, self.quit_code]
            elif self.nb_ans == 4:
                self.left_key_name = "a"
                self.left_key_code = "a"
                self.mid_left_key_name = "z"
                self.mid_left_key_code = "z"
                self.mid_right_key_name = "o"
                self.mid_right_key_code = "o"
                self.right_key_name = "p"
                self.right_key_code = "p"
                self.quit_code = "q"
                self.flag_code = "f"
                self.yes_key_code = "p"
                self.yes_key_name = "p"
                self.keys = [self.left_key_code, self.mid_left_key_code, self.right_key_code, self.mid_right_key_code,
                             self.flag_code, self.quit_code]

        ### EYE TRACKER

        eyetrackers = tobii_research.find_all_eyetrackers()

        if len(eyetrackers) == 0:
            raise RuntimeError('No Tobii eyetrackers')
        self.eyetracker = eyetrackers[0]
        self.calibration = tobii_research.ScreenBasedCalibration(self.eyetracker)

    def update_csv(self, *args):
        args = list(map(str, args))
        self.dataFile.write(",".join(args))
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

    def create_visual_text(self, text, pos=(0, 0), font_size=0.06, color="white", units='height', autolog=None):
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
            autoLog=autolog,
        )

    def create_visual_image(self, image, pos=(0, 0), ori=0.0, units='pix', size=None, autolog=None):
        return visual.ImageStim(
            win=self.win,
            image=image,
            size=size,
            pos=pos,
            ori=ori,
            units=units,
            autoLog=autolog,
            )

    def create_visual_rect(self, size, lineColor, fillColor, units="height", autolog=None):
        return visual.Rect(
            win=self.win,
            width=300,
            height=100,
            size=size,
            units=units,
            lineColor=lineColor,
            fillColor=fillColor,
            autoLog=autolog,
        )

    def create_visual_circle(self, size, units, fillcolor, pos=None, autolog=None):
        return visual.Circle(
            win=self.win,
            size=size,
            units=units,
            radius=30,
            fillColor=fillcolor,
            lineWidth=0,
            pos=pos,
            autoLog=autolog,
        )

    def check_break(self, no_trial, first_threshold, second_threshold=None, test=False):
        if no_trial == first_threshold:
            self.create_visual_text("2 minutes de pause").draw()
            self.win.flip()
            if not test:
                core.wait(60)  # two minuts break
            else:
                core.wait(10)
            self.create_visual_text("Plus qu'une minute !").draw()
            self.win.flip()
            if not test:
                core.wait(60)
            else:
                core.wait(10)

        elif second_threshold is not None and no_trial == second_threshold:
            self.create_visual_text("2 minutes de pause").draw()
            self.win.flip()
            if not test:
                core.wait(60)  # two minuts break
            else:
                core.wait(10)
            self.create_visual_text("Plus qu'une minute !").draw()
            self.win.flip()
            if not test:
                core.wait(60)
            else:
                core.wait(10)

    def wait_yes(self, key):
        """wait until user presses <self.yes_key_code>
        """
        while self.get_response(self.response_pad) != key:
            pass

    def quit_experiment(self):
        """Ends the experiment
        """
        self.close_datafile()
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
            self.dev.flush_serial_buffer()
            while not self.dev.has_response():
                self.dev.poll_for_response()
            resp = self.dev.get_next_response()
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

    ##############################################################################
    ###########                 EYE TRACKER METHODS                ###############
    ##############################################################################

    def show_status(self, text_color='white', enable_mouse=False):
        """
        Draw eyetracker status on the screen.

        :param text_color: Color of message text. Default value is 'white'
        :param bool enable_mouse: If True, mouse operation is enabled.
            Default value is False.
        """

        if self.eyetracker is None:
            raise RuntimeError('Eyetracker is not found.')

        if enable_mouse:
            mouse = event.Mouse(visible=False, win=self.win)

        self.gaze_data_status = None
        self.eyetracker.subscribe_to(tobii_research.EYETRACKER_GAZE_DATA,
                                     self.on_gaze_data_status)

        msg = self.create_visual_text(text="", pos=(0, -0.35), color=text_color, units="height", font_size=0.02,
                                      autolog=False)
        bgrect = self.create_visual_rect(size=(0.6, 0.6), lineColor="white", fillColor="black", units="height",
                                         autolog=False)
        leye = self.create_visual_circle(size=0.05, units='height', fillcolor="red", autolog=False)
        reye = self.create_visual_circle(size=0.05, units='height', fillcolor="yellow", autolog=False)

        b_show_status = True
        while b_show_status:
            bgrect.draw()
            if self.gaze_data_status is not None:
                lp, lv, rp, rv = self.gaze_data_status
                msgst = 'Left: {:.3f},{:.3f},{:.3f}\n'.format(*lp)
                msgst += 'Right: {:.3f},{:.3f},{:.3f}\n'.format(*rp)
                msg.setText(msgst)
                if lv:
                    leye.setPos(((lp[0] - 0.5) / 2, (lp[1] - 0.5) / 2))
                    leye.setRadius((1 - lp[2]) / 2)
                    leye.draw()
                if rv:
                    reye.setPos(((rp[0] - 0.5) / 2, (rp[1] - 0.5) / 2))
                    reye.setRadius((1 - rp[2]) / 2)
                    reye.draw()

            for key in event.getKeys():
                if key == 'escape' or key == 'space':
                    b_show_status = False

            if enable_mouse and mouse.getPressed()[0]:
                b_show_status = False

            msg.draw()
            self.win.flip()

        self.eyetracker.unsubscribe_from(tobii_research.EYETRACKER_GAZE_DATA)

    def on_gaze_data_status(self, gaze_data):
        """
        Callback function used by
        :func:`~psychopy_tobii_controller.tobii_controller.show_status`

        Usually, users don't have to call this method.
        """

        lp = gaze_data.left_eye.gaze_origin.position_in_track_box_coordinates
        lv = gaze_data.left_eye.gaze_origin.validity
        rp = gaze_data.right_eye.gaze_origin.position_in_track_box_coordinates
        rv = gaze_data.right_eye.gaze_origin.validity
        self.gaze_data_status = (lp, lv, rp, rv)

    def run_calibration(self, calibration_points, move_duration=1.5,
                        shuffle=True, start_key='space', decision_key='space',
                        text_color='white', enable_mouse=False):
        """
        Run calibration.

        :param calibration_points: List of position of calibration points.
        :param float move_duration: Duration of animation of calibration target.
            Unit is second.  Default value is 1.5.
        :param bool shuffle: If True, order of calibration points is shuffled.
            Otherwise, calibration target moves in the order of calibration_points.
            Default value is True.
        :param str start_key: Name of key to start calibration procedure.
            If None, calibration starts immediately afte this method is called.
            Default value is 'space'.
        :param str decision_key: Name of key to accept/retry calibration.
            Default value is 'space'.
        :param text_color: Color of message text. Default value is 'white'
        :param bool enable_mouse: If True, mouse operation is enabled.
            Default value is False.
        """
        if self.eyetracker is None:
            raise RuntimeError('Eyetracker is not found.')

        if not (2 <= len(calibration_points) <= 9):
            raise ValueError('Calibration points must be 2~9')

        if enable_mouse:
            mouse = event.Mouse(visible=False, win=self.win)

        img = Image.new('RGBA', tuple(self.win.size))
        img_draw = ImageDraw.Draw(img)

        result_img = visual.SimpleImageStim(self.win, img, autoLog=False)
        result_msg = visual.TextStim(self.win, pos=(0, -self.win.size[1] / 4),
                                              color=text_color, units='pix', autoLog=False)
        # result_img = self.create_visual_image(img, autolog=False)
        # result_msg = self.create_visual_text(text="", pos=(0, -self.win.size[1] / 4), color=text_color,
        # units="height", autolog=False)
        # should be PIX
        remove_marker = visual.Circle(
            self.win, radius=self.calibration_target_dot.radius * 5,
            fillColor='black', lineColor='white', lineWidth=1, autoLog=False)
        if self.win.units == 'norm':  # fix oval
            remove_marker.setSize([float(self.win.size[1]) / self.win.size[0], 1.0])
            remove_marker.setSize([float(self.win.size[1]) / self.win.size[0], 1.0])

        self.calibration.enter_calibration_mode()

        self.move_duration = move_duration
        self.original_calibration_points = calibration_points[:]
        self.retry_points = list(range(len(self.original_calibration_points)))  # set all points

        in_calibration_loop = True
        while in_calibration_loop:
            self.calibration_points = []
            for i in range(len(self.original_calibration_points)):
                if i in self.retry_points:
                    self.calibration_points.append(self.original_calibration_points[i])

            if shuffle:
                np.random.shuffle(self.calibration_points)

            if start_key is not None or enable_mouse:
                waitkey = True
                if start_key is not None:
                    if enable_mouse:
                        result_msg.setText('Press {} or click left button to start calibration'.format(start_key))
                    else:
                        result_msg.setText('Press {} to start calibration'.format(start_key))
                else:  # enable_mouse==True
                    result_msg.setText('Click left button to start calibration')
                while waitkey:
                    for key in event.getKeys():
                        if key == start_key:
                            waitkey = False

                    if enable_mouse and mouse.getPressed()[0]:
                        waitkey = False

                    result_msg.draw()
                    self.win.flip()
            else:
                self.win.flip()

            self.update_calibration()

            calibration_result = self.calibration.compute_and_apply()

            self.win.flip()

            img_draw.rectangle(((0, 0), tuple(self.win.size)), fill=(0, 0, 0, 0))
            if calibration_result.status == tobii_research.CALIBRATION_STATUS_FAILURE:
                # computeCalibration failed.
                pass
            else:
                if len(calibration_result.calibration_points) == 0:
                    pass
                else:
                    for calibration_point in calibration_result.calibration_points:
                        p = calibration_point.position_on_display_area
                        for calibration_sample in calibration_point.calibration_samples:
                            lp = calibration_sample.left_eye.position_on_display_area
                            rp = calibration_sample.right_eye.position_on_display_area
                            if calibration_sample.left_eye.validity == tobii_research.VALIDITY_VALID_AND_USED:
                                img_draw.line(((p[0] * self.win.size[0], p[1] * self.win.size[1]),
                                               (lp[0] * self.win.size[0], lp[1] * self.win.size[1])),
                                              fill=(0, 255, 0, 255))
                            if calibration_sample.right_eye.validity == tobii_research.VALIDITY_VALID_AND_USED:
                                img_draw.line(((p[0] * self.win.size[0], p[1] * self.win.size[1]),
                                               (rp[0] * self.win.size[0], rp[1] * self.win.size[1])),
                                              fill=(255, 0, 0, 255))
                        img_draw.ellipse(((p[0] * self.win.size[0] - 3, p[1] * self.win.size[1] - 3),
                                          (p[0] * self.win.size[0] + 3, p[1] * self.win.size[1] + 3)),
                                         outline=(0, 0, 0, 255))

            if enable_mouse:
                result_msg.setText(
                    'Accept/Retry: {} or right-click\nSelect recalibration points: 0-9 key or left-click\nAbort: esc'.format(
                        decision_key))
            else:
                result_msg.setText(
                    'Accept/Retry: {}\nSelect recalibration points: 0-9 key\nAbort: esc'.format(decision_key))
            result_img.setImage(img)

            waitkey = True
            self.retry_points = []
            if enable_mouse:
                mouse.setVisible(True)
            while waitkey:
                for key in event.getKeys():
                    if key in [decision_key, 'escape']:
                        waitkey = False
                    elif key in ['0', 'num_0']:
                        if len(self.retry_points) == 0:
                            self.retry_points = list(range(len(self.original_calibration_points)))
                        else:
                            self.retry_points = []
                    elif key in self.key_index_dict:
                        key_index = self.key_index_dict[key]
                        if key_index < len(self.original_calibration_points):
                            if key_index in self.retry_points:
                                self.retry_points.remove(key_index)
                            else:
                                self.retry_points.append(key_index)
                if enable_mouse:
                    pressed = mouse.getPressed()
                    if pressed[2]:  # right click
                        key = decision_key
                        waitkey = False
                    elif pressed[0]:  # left click
                        mouse_pos = mouse.getPos()
                        for key_index in range(len(self.original_calibration_points)):
                            p = self.original_calibration_points[key_index]
                            if np.linalg.norm([mouse_pos[0] - p[0],
                                               mouse_pos[1] - p[1]]) < self.calibration_target_dot.radius * 5:
                                if key_index in self.retry_points:
                                    self.retry_points.remove(key_index)
                                else:
                                    self.retry_points.append(key_index)
                                time.sleep(0.2)
                                break
                result_img.draw()
                if len(self.retry_points) > 0:
                    for index in self.retry_points:
                        if index > len(self.original_calibration_points):
                            self.retry_points.remove(index)
                        remove_marker.setPos(self.original_calibration_points[index])
                        remove_marker.draw()
                result_msg.draw()
                self.win.flip()

            if key == decision_key:
                if len(self.retry_points) == 0:
                    retval = 'accept'
                    in_calibration_loop = False
                else:  # retry
                    for point_index in self.retry_points:
                        x, y = self.get_tobii_pos(self.original_calibration_points[point_index])
                        self.calibration.discard_data(x, y)
            elif key == 'escape':
                retval = 'abort'
                in_calibration_loop = False
            else:
                raise RuntimeError('Calibration: Invalid key')

            if enable_mouse:
                mouse.setVisible(False)

        self.calibration.leave_calibration_mode()

        if enable_mouse:
            mouse.setVisible(False)

        return retval

    def collect_calibration_data(self, p, cood='PsychoPy'):
        """
        Callback function used by
        :func:`~psychopy_tobii_controller.tobii_controller.run_calibration`

        Usually, users don't have to call this method.
        """

        if cood == 'PsychoPy':
            self.calibration.collect_data(*self.get_tobii_pos(p))
        elif cood == 'Tobii':
            self.calibration.collect_data(*p)
        else:
            raise ValueError('cood must be \'PsychoPy\' or \'Tobii\'')

    def update_calibration_default(self):
        """
        Updating calibration target and correcting calibration data.
        This method is called by
        :func:`~psychopy_tobii_controller.tobii_controller.run_calibration`

        Usually, users don't have to call this method.
        """

        clock = core.Clock()
        for point_index in range(len(self.calibration_points)):
            x, y = self.get_tobii_pos(self.calibration_points[point_index])
            self.calibration_target_dot.setPos(self.calibration_points[point_index])
            self.calibration_target_disc.setPos(self.calibration_points[point_index])
            clock.reset()
            current_time = clock.getTime()
            while current_time < self.move_duration:
                self.calibration_target_disc.setRadius(
                    (self.calibration_target_dot_size * 2.0 - self.calibration_target_disc_size) / \
                    self.move_duration * current_time + self.calibration_target_disc_size
                )
                event.getKeys()
                self.calibration_target_disc.draw()
                self.calibration_target_dot.draw()
                self.win.flip()
                current_time = clock.getTime()
            self.calibration.collect_data(x, y)

    def set_custom_calibration(self, func):
        """
        Set custom calibration function.

        :param func: custom calibration function.
        """

        self.update_calibration = types.MethodType(func, self)

    def use_default_calibration(self):
        """
        Revert calibration function to default one.
        """
        self.update_calibration = self.update_calibration_default

    def get_calibration_keymap(self):
        """
        Get current key mapping for selecting calibration points as a dict object.
        """

        return self.key_index_dict.copy()

    def set_calibration_keymap(self, keymap):
        """
        Set key mapping for selecting calibration points.

        :param dict keymap: Dict object that holds calibration keymap.
            Key of the dict object correspond to PsychoPy key name.
            Value is index of the list of calibration points.
            For example, if you have only two calibration points and
            want to select these points by 'z' and 'x' key, set keymap
            {'z':0, 'x':1}.
        """

        self.key_index_dict = keymap.copy()

    def use_default_calibration_keymap(self):
        """
        Set default key mapping for selecting calibration points.
        """

        self.key_index_dict = default_key_index_dict.copy()

    def set_calibration_param(self, param_dict):
        """
        Set calibration parameters.

        :param dict param_dict: Dict object that holds calibration parameters.
            Use :func:`~psychopy_tobii_controller.tobii_controller.get_calibration_param`
            to get dict object.
        """
        self.calibration_target_dot_size = param_dict['dot_size']
        self.calibration_target_dot.lineColor = param_dict['dot_line_color']
        self.calibration_target_dot.fillColor = param_dict['dot_fill_color']
        self.calibration_target_dot.lineWidth = param_dict['dot_line_width']
        self.calibration_target_disc_size = param_dict['disc_size']
        self.calibration_target_disc.lineColor = param_dict['disc_line_color']
        self.calibration_target_disc.fillColor = param_dict['disc_fill_color']
        self.calibration_target_disc.lineWidth = param_dict['disc_line_width']

    def get_calibration_param(self):
        """
        Get calibration parameters as a dict object.
        The dict object has following keys.

        - 'dot_size': size of the center dot of calibration target.
        - 'dot_line_color': line color of the center dot of calibration target.
        - 'dot_fill_color': fill color of the center dot of calibration target.
        - 'dot_line_width': line width of the center dot of calibration target.
        - 'disc_size': size of the surrounding disc of calibration target.
        - 'disc_line_color': line color of the surrounding disc of calibration target
        - 'disc_fill_color': fill color of the surrounding disc of calibration target
        - 'disc_line_width': line width of the surrounding disc of calibration target
        - 'text_color': color of text
        """

        param_dict = {'dot_size': self.calibration_target_dot_size,
                      'dot_line_color': self.calibration_target_dot.lineColor,
                      'dot_fill_color': self.calibration_target_dot.fillColor,
                      'dot_line_width': self.calibration_target_dot.lineWidth,
                      'disc_size': self.calibration_target_disc_size,
                      'disc_line_color': self.calibration_target_disc.lineColor,
                      'disc_fill_color': self.calibration_target_disc.fillColor,
                      'disc_line_width': self.calibration_target_disc.lineWidth}
        return param_dict

    def subscribe(self):
        """
        Start recording.
        """

        self.gaze_data = []
        self.event_data = []
        self.recording = True
        self.eyetracker.subscribe_to(tobii_research.EYETRACKER_GAZE_DATA, self.on_gaze_data)

    def unsubscribe(self):
        """
        Stop recording.
        """

        self.eyetracker.unsubscribe_from(tobii_research.EYETRACKER_GAZE_DATA)
        self.recording = False
        self.flush_data()
        self.gaze_data = []
        self.event_data = []

    def on_gaze_data(self, gaze_data):
        """
        Callback function used by
        :func:`~psychopy_tobii_controller.tobii_controller.subscribe`

        Usually, users don't have to call this method.
        """

        t = gaze_data.system_time_stamp
        lx = gaze_data.left_eye.gaze_point.position_on_display_area[0]
        ly = gaze_data.left_eye.gaze_point.position_on_display_area[1]
        lp = gaze_data.left_eye.pupil.diameter
        lv = gaze_data.left_eye.gaze_point.validity
        rx = gaze_data.right_eye.gaze_point.position_on_display_area[0]
        ry = gaze_data.right_eye.gaze_point.position_on_display_area[1]
        rp = gaze_data.right_eye.pupil.diameter
        rv = gaze_data.right_eye.gaze_point.validity
        self.gaze_data.append((t, lx, ly, lp, lv, rx, ry, rp, rv))

    def get_current_gaze_position(self):
        """
        Get current (i.e. the latest) gaze position as a tuple of
        (left_x, left_y, right_x, right_y).
        Values are numpy.nan if Tobii fails to get gaze position.
        """

        if len(self.gaze_data) == 0:
            return (np.nan, np.nan, np.nan, np.nan)
        else:
            lxy = self.get_psychopy_pos(self.gaze_data[-1][1:3])
            rxy = self.get_psychopy_pos(self.gaze_data[-1][5:7])
            return (lxy[0], lxy[1], rxy[0], rxy[1])

    def get_current_pupil_size(self):
        """
        Get current (i.e. the latest) pupil size as a tuple of
        (left, right).
        Values are numpy.nan if Tobii fails to get pupil size.
        """

        if len(self.gaze_data) == 0:
            return (None, None)
        else:
            return (self.gaze_data[-1][3],  # lp
                    self.gaze_data[-1][7])  # rp

    def open_datafile(self, filename, embed_events=False):
        """
        Open data file.

        :param str filename: Name of data file to be opened.
        :param bool embed_events: If True, event data is
            embeded in gaze data.  Otherwise, event data is
            separately output after gaze data.
        """

        if self.datafile is not None:
            self.close_datafile()

        self.embed_events = embed_events
        self.datafile = open(filename, 'w')

    def close_datafile(self):
        """
        Write data to the data file and close the data file.
        """

        if self.datafile is not None:
            self.flush_data()
            self.datafile.close()

        self.datafile = None

    def record_event(self, event):
        """
        Record events with timestamp.

        Note: This method works only during recording.

        :param str event: Any string.
        """
        if not self.recording:
            return

        self.event_data.append((tobii_research.get_system_time_stamp(), event))

    def flush_data(self):
        """
        Write data to the data file.

        Note: This method do nothing during recording.
        """

        if self.datafile is None:
            warnings.warn('data file is not set.')
            return

        if len(self.gaze_data) == 0:
            return

        if self.recording:
            return


        if self.embed_events:
            self.datafile.write('\t'.join(['TimeStamp',
                                           'GazePointXLeft',
                                           'GazePointYLeft',
                                           'PupilLeft',
                                           'ValidityLeft',
                                           'GazePointXRight',
                                           'GazePointYRight',
                                           'PupilRight',
                                           'ValidityRight',
                                           'GazePointX',
                                           'GazePointY',
                                           'Event']) + '\n')
        else:
            self.datafile.write('\t'.join(['TimeStamp',
                                           'GazePointXLeft',
                                           'GazePointYLeft',
                                           'PupilLeft',
                                           'ValidityLeft',
                                           'GazePointXRight',
                                           'GazePointYRight',
                                           'PupilRight',
                                           'ValidityRight',
                                           'GazePointX',
                                           'GazePointY']) + '\n')

        format_string = '%.1f\t%.4f\t%.4f\t%.4f\t%d\t%.4f\t%.4f\t%.4f\t%d\t%.4f\t%.4f'

        timestamp_start = self.gaze_data[0][0]
        num_output_events = 0
        if self.embed_events:
            for i in range(len(self.gaze_data)):
                if num_output_events < len(self.event_data) and self.event_data[num_output_events][0] < \
                        self.gaze_data[i][0]:
                    event_t = self.event_data[num_output_events][0]
                    event_text = self.event_data[num_output_events][1]

                    if i > 0:
                        output_data = self.convert_tobii_record(
                            self.interpolate_gaze_data(self.gaze_data[i - 1], self.gaze_data[i], event_t),
                            timestamp_start)
                    else:
                        output_data = ((event_t - timestamp_start) / 1000.0, np.nan, np.nan, np.nan, 0,
                                       np.nan, np.nan, np.nan, 0, np.nan, np.nan)

                    self.datafile.write(format_string % output_data)
                    print('kaka')
                    self.datafile.write('\t%s\n' % (event_text))

                    num_output_events += 1

                self.datafile.write(format_string % self.convert_tobii_record(self.gaze_data[i], timestamp_start))
                self.datafile.write('\t\n')

            # flush remaining events
            if num_output_events < len(self.event_data):
                for e_i in range(num_output_events, len(self.event_data)):
                    event_t = self.event_data[e_i][0]
                    event_text = self.event_data[e_i][1]

                    output_data = ((event_t - timestamp_start) / 1000.0, np.nan, np.nan, np.nan, 0,
                                   np.nan, np.nan, np.nan, 0, np.nan, np.nan)
                    self.datafile.write(format_string % output_data)
                    self.datafile.write('\t%s\n' % (event_text))
        else:
            for i in range(len(self.gaze_data)):
                self.datafile.write(format_string % self.convert_tobii_record(self.gaze_data[i], timestamp_start))
                self.datafile.write('\n')

            self.datafile.write('TimeStamp\tEvent\n')
            for e in self.event_data:
                self.datafile.write('%.1f\t%s\n' % ((e[0] - timestamp_start) / 1000.0, e[1]))

        self.datafile.flush()

    def get_psychopy_pos(self, p):
        """
        Convert PsychoPy position to Tobii coordinate system.

        :param p: Position (x, y)
        """

        p = (p[0], 1 - p[1])  # flip vert
        if self.win.units == 'norm':
            return (2 * p[0] - 1, 2 * p[1] - 1)
        elif self.win.units == 'height':
            return ((p[0] - 0.5) * self.win.size[0] / self.win.size[1], p[1] - 0.5)

        p_pix = ((p[0] - 0.5) * self.win.size[0], (p[1] - 0.5) * self.win.size[1])
        if self.win.units == 'pix':
            return p_pix
        elif self.win.units == 'cm':
            return (pix2cm(p_pix[0], self.win.monitor), pix2cm(p_pix[1], self.win.monitor))
        elif self.win.units == 'deg':
            return (pix2deg(p_pix[0], self.win.monitor), pix2deg(p_pix[1], self.win.monitor))
        elif self.win.units in ['degFlat', 'degFlatPos']:
            return (pix2deg(np.array(p_pix), self.win.monitor, correctFlat=True))
        else:
            raise ValueError('unit ({}) is not supported.'.format(self.win.units))

    def get_tobii_pos(self, p):
        """
        Convert Tobii position to PsychoPy coordinate system.

        :param p: Position (x, y)
        """

        if self.win.units == 'norm':
            gp = ((p[0] + 1) / 2, (p[1] + 1) / 2)
        elif self.win.units == 'height':
            gp = (p[0] * self.win.size[1] / self.win.size[0] + 0.5, p[1] + 0.5)
        elif self.win.units == 'pix':
            gp = (p[0] / self.win.size[0] + 0.5, p[1] / self.win.size[1] + 0.5)
        elif self.win.units == 'cm':
            p_pix = (cm2pix(p[0], self.win.monitor), cm2pix(p[1], self.win.monitor))
            gp = (p_pix[0] / self.win.size[0] + 0.5, p_pix[1] / self.win.size[1] + 0.5)
        elif self.win.units == 'deg':
            p_pix = (deg2pix(p[0], self.win.monitor), deg2pix(p[1], self.win.monitor))
            gp = (p_pix[0] / self.win.size[0] + 0.5, p_pix[1] / self.win.size[1] + 0.5)
        elif self.win.units in ['degFlat', 'degFlatPos']:
            p_pix = (deg2pix(np.array(p), self.win.monitor, correctFlat=True))
            gp = (p_pix[0] / self.win.size[0] + 0.5, p_pix[1] / self.win.size[1] + 0.5)
        else:
            raise ValueError('unit ({}) is not supported'.format(self.win.units))

        return (gp[0], 1 - gp[1])  # flip vert

    def convert_tobii_record(self, record, start_time):
        """
        Convert tobii data to output style.
        Usually, users don't have to call this method.

        :param record: element of self.gaze_data.
        :param start_time: Tobii's timestamp when recording was started.
        """

        lxy = self.get_psychopy_pos(record[1:3])
        rxy = self.get_psychopy_pos(record[5:7])

        if record[4] == 0 and record[8] == 0:  # not detected
            ave = (np.nan, np.nan)
        elif record[4] == 0:
            ave = rxy
        elif record[8] == 0:
            ave = lxy
        else:
            ave = ((lxy[0] + rxy[0]) / 2.0, (lxy[1] + rxy[1]) / 2.0)

        return ((record[0] - start_time) / 1000.0,
                lxy[0], lxy[1], record[3], record[4],
                rxy[0], rxy[1], record[7], record[8],
                ave[0], ave[1])

    def interpolate_gaze_data(self, record1, record2, t):
        """
        Interpolate gaze data between record1 and record2.
        Usually, users don't have to call this method.

        :param record1: element of self.gaze_data.
        :param record2: element of self.gaze_data.
        :param t: timestamp to calculate interpolation.
        """

        w1 = (record2[0] - t) / (record2[0] - record1[0])
        w2 = (t - record1[0]) / (record2[0] - record1[0])

        # left eye
        if record1[4] == 0 and record2[4] == 0:
            ldata = record1[1:5]
        elif record1[4] == 0:
            ldata = record2[1:5]
        elif record2[4] == 0:
            ldata = record1[1:5]
        else:
            ldata = (w1 * record1[1] + w2 * record2[1],
                     w1 * record1[2] + w2 * record2[2],
                     w1 * record1[3] + w2 * record2[3],
                     1)

        # right eye
        if record1[8] == 0 and record2[8] == 0:
            rdata = record1[5:9]
        elif record1[4] == 0:
            rdata = record2[5:9]
        elif record2[4] == 0:
            rdata = record1[5:9]
        else:
            rdata = (w1 * record1[5] + w2 * record2[5],
                     w1 * record1[6] + w2 * record2[6],
                     w1 * record1[7] + w2 * record2[7],
                     1)

        return (t,) + ldata + rdata

    def task(self, no_trial):
        """Method to overwrite to implement your cognitive task.
        :param no_trial: Trial number (starting from 0).
        """

    def example(self):
        """Method to overwrite to implement an example in your cognitive task. Will be launch only if
        <self.launch_example> is True.
        """

    def start(self):
        ## EYE TRACKER PART ###
        self.open_datafile(f"csv_eyetracker/{self.file_name}.tsv", embed_events=False)
        self.set_calibration_keymap({'num_7': 0, 'num_9': 1, 'num_5': 2, 'num_1': 3, 'num_3': 4})
        self.show_status()
        ret = self.run_calibration([(0, 0), (-0.4, 0.4), (0.4, 0.4), (0.0, 0.0), (-0.4, -0.4), (0.4, -0.4)])

        if ret == "abort":
            sys.exit()
        marker = visual.Rect(self.win, size=(0.01, 0.01))
        self.subscribe()

        waitkey = True
        while waitkey:
            # Get the latest gaze position data.
            currentGazePosition = self.get_current_gaze_position()

            # Gaze position is a tuple of four values (lx, ly, rx, ry).
            # The value is numpy.nan if Tobii failed to detect gaze position.
            if not np.nan in currentGazePosition:
                marker.setPos(currentGazePosition[0:2])
                marker.setLineColor('white')
            else:
                marker.setLineColor('red')
            keys = event.getKeys()
            if 'space' in keys:
                waitkey = False
            elif len(keys) >= 1:
                # Record the first key name to the data file.
                self.record_event(keys[0])

            marker.draw()
            self.win.flip()

        ## EYE TRACKER END ###
        self.win.winHandle.set_fullscreen(True)
        self.win.flip()
        self.win.mouseVisible = False
        self.create_visual_text(self.welcome).draw()
        self.win.flip()
        core.wait(2)
        next = self.create_visual_text(self.next, (0, -0.4), 0.04)
        flag = self.create_visual_text(self.flag, (0, 0.4), 0.04)
        for instr in self.instructions:
            self.create_visual_text(instr, font_size=self.font_size_instr).draw()
            next.draw()
            self.win.flip()
            self.wait_yes(self.yes_key_code)
        if self.launch_example:
            self.example()
        self.create_visual_text(self.good_luck).draw()
        flag.draw()
        self.win.flip()
        self.wait_yes(self.flag_code)
        self.win.flip()
        core.wait(2)
        for i in range(self.trials):
            self.task(i)
        self.create_visual_text(self.end).draw()
        self.win.flip()
        core.wait(60)
        self.dataFile.close()
        self.unsubscribe()
        self.close_datafile()
        self.quit_experiment()

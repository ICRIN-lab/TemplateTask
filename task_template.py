from psychopy import visual, gui, data, event

import os


class TaskTemplate:
    """
    A cognitive task template, to use to code cognitive tasks more simply
    """
    bg = "black"
    """Set window background. Default value is black."""
    text_color = "white"
    """Set text color from create_visual_text method. Default value is white."""
    yes_key_code = "o"
    """Set code for "yes" key. Default value is "o".("""
    yes_key_name = "bleue"
    """Set name for "yes" key. Default value is "bleue" (blue in french)."""
    no_key_code = "n"
    """Set code for "no" key. Default value is "n". """
    no_key_name = "verte"
    """Set name for "no" key. Default value is "verte" (green in french)."""
    keys = [yes_key_code, no_key_code]
    instructions = []
    trials = 10
    example = False

    def __init__(self, csv_folder, example=None):
        """
        :param example: Can overwrite default <self.example> value.
        """
        self.win = visual.Window(
            size=[1920, 1080],  # if needed, change the size in corcondance with your monitor
            fullscr=False,
            units="pix",
            screen=0,
            allowStencil=False,
            monitor='testMonitor',
            color=self.bg,
            colorSpace='rgb'
        )
        self.start = None
        exp_info = {'participant': '', "date": data.getDateStr()}
        gui.DlgFromDict(exp_info, title='Subliminal Priming Task', fixed=["date"])
        self.participant = exp_info["participant"]
        file_name = exp_info['participant'] + '_' + exp_info['date']
        self.dataFile = open(f"{csv_folder}/{file_name}.csv", 'w')
        if example is not None:
            self.example = example

    def create_visual_text(self, text, pos=(0, 0), font_size=0.06):
        """
        Create a <visual.TextStim> with some default parameters so it's simpler to create visual texts
        """
        return visual.TextStim(
            win=self.win,
            text=text,
            font='Arial',
            units='height',
            pos=pos,
            height=font_size,
            wrapWidth=None,
            ori=0,
            color=self.text_color,
            colorSpace='rgb',
            opacity=1,
            languageStyle='LTR',
            depth=0.0
        )

    def wait(self):
        """wait until user presses <self.yes_key_code>"""
        while self.get_response() != self.yes_key_code:
            pass

    @staticmethod
    def quit_experiment():
        """
        Ends the experiment
        """
        exit()

    def get_response(self, keys=None):
        """Waits for a response from the participant.
        Pressing Q while the function is wait for a response will quit the experiment.
        Returns the pressed key and the reaction time.
        """
        if keys is None:
            keys = self.keys
        resp = event.waitKeys(keyList=keys, clearEvents=True)
        if resp[0] == "q":
            self.quit_experiment()
        return resp[0]
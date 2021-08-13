from psychopy import visual, gui, data, event, core
import time


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
    launch_example = False
    """Whether your task should show an example. If True, you should overwrite the example method. Can be overwritten 
    at init"""
    welcome = "Bienvenue !"
    """Welcome text shown when the task is started."""
    instructions = []
    """instructions on the task given to the user. Should be overwritten as it is empty in template."""
    next = f"Pour passer à l'instruction suivante, appuyez sur la touche {yes_key_name}"
    """text to show between 2 screens of instructions."""
    good_luck = "Bonne chance !"
    """Good luck text to show right before first trial"""
    end = "Le mini-jeu est à présent terminé. Merci, et au revoir !"
    """Text to show when all trials are done, and before the end."""
    csv_headers = []
    """Headers of CSV file. Should be overwritten as it is empty in this template."""

    def __init__(self, csv_folder, launch_example=None):
        """
        :param launch_example: Can overwrite default <self.example> value.
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
        exp_info = {'participant': '', "date": data.getDateStr()}
        gui.DlgFromDict(exp_info, title='Subliminal Priming Task', fixed=["date"])
        self.participant = exp_info["participant"]
        file_name = exp_info['participant'] + '_' + exp_info['date']
        self.dataFile = open(f"{csv_folder}/{file_name}.csv", 'w')
        self.dataFile.write(", ".join(self.csv_headers))
        self.dataFile.write("\n")
        if launch_example is not None:
            self.launch_example = launch_example

    def update_csv(self, *args):
        self.dataFile.write(", ".join(args))
        self.dataFile.write("\n")

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

    def wait_yes(self):
        """wait until user presses <self.yes_key_code>
        """
        while self.get_response() != self.yes_key_code:
            pass

    def quit_experiment(self):
        """Ends the experiment
        """
        self.dataFile.close()
        exit()

    def get_response(self, keys=None, timeout=float("inf")):
        """Waits for a response from the participant.
        Pressing Q while the function is wait for a response will quit the experiment.
        Returns the pressed key.
        """
        if keys is None:
            keys = self.keys
        resp = event.waitKeys(keyList=keys, clearEvents=True, maxWait=timeout)
        if resp is None:
            return
        if resp[0] == self.quit_code:
            self.quit_experiment()
        return resp[0]

    def get_response_with_time(self, keys=None, timeout=float("inf")):
        """Waits for a response from the participant.
                Pressing Q while the function is wait for a response will quit the experiment.
                Returns the pressed key and time (in seconds) since the method has been launched.
                """
        if keys is None:
            keys = self.keys
        clock = core.Clock()
        resp = event.waitKeys(timeout, keys,  timeStamped=clock)
        if resp is None:
            return
        if resp[0][0] == self.quit_code:
            self.quit_experiment()
        return resp[0]

    def task(self, no_trial, exp_start_timestamp, trial_start_timestamp):
        """Method to overwrite to implement your cognitive task.
        :param trial_start_timestamp: Timestamp got right before this trial
        :param exp_start_timestamp: Timestamp got right before first trial
        :param no_trial: Trial number (starting from 0).
        """
        pass

    def example(self):
        """Method to overwrite to implement an example in your cognitive task. Will be launch only if
        <self.launch_example> is True.
        """
        pass

    def start(self):
        self.win.winHandle.set_fullscreen(True)
        self.win.flip()
        self.win.mouseVisible = False
        self.create_visual_text(self.welcome).draw()
        self.win.flip()
        core.wait(2)
        next = self.create_visual_text(self.next)
        for instr in self.instructions:
            self.create_visual_text(instr, (0, -0.4), 0.04).draw()
            next.draw()
            self.win.flip()
            self.wait_yes()
        if self.launch_example:
            self.example()
        self.create_visual_text(self.good_luck).draw()
        self.win.flip()
        exp_start_timestamp = time.time()
        for i in range(self.trials):
            trial_start_timestamp = time.time()
            self.task(i, exp_start_timestamp, trial_start_timestamp)
        self.create_visual_text(self.end).draw()
        self.win.flip()
        core.wait(2)
        self.dataFile.close()
        self.quit_experiment()

# TemplateTask

TemplateTask is an open-source template for creating experiments in behavioral science. 
It aims to provide a template for developping cognitive tasks.

To meet this goal, TemplateTask provides a template which you can use to write your experiments in Python code. 
The entire template is written in Python.

TemplateTask uses the [PsychoPy library](https://psychopy.org/index.html):

*Peirce, J. W., Gray, J. R., Simpson, S., MacAskill, M. R., Höchenberger, R., Sogo, H., Kastman, E., Lindeløv, J. (2019). PsychoPy2: experiments in behavior made easy. Behavior Research Methods. 10.3758/s13428-018-01193-y*

Make sure to download the package [here](https://www.psychopy.org/download.html) before using our template.

ALSO EXPLAIN THAT YOU NEED TO DOWNLOAD IT FOR OTHER TAKS TO WORK AND EXPLAIN HOW TO DL.

## Contributions

To contribute, please fork the repository, hack in a feature branch, and send a
pull request.

## The code 

### Imports

```python
from psychopy import visual, gui, data, event, core
import time
```

### TaskTemplate class 

```python
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
```

```python
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
        self.init()
```

```python

    def init(self):
        """Function launched at the end of constructor if you want to create instance variables or execute some code
        at initialization"""
```


## More information

* Homepage: http://icrin.fr/

## Contact us 

* Mail : <contact@icrin.fr>
* Twitter : <https://twitter.com/RedwanMaatoug>

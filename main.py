import logging
from functools import partial

from build123d import *
from ocp_vscode import show, Camera
from OCP import Message  # Make things less verbose

from cover import Cover
from switch import PowerSwitch
from button import Button


# --| Boilerplate |----------------------------------------
for printer in Message.Message.DefaultMessenger_s().Printers():
    printer.SetTraceLevel(Message.Message_Gravity(3))
log = logging.getLogger(__name__)
logging.getLogger("build123d").setLevel(logging.WARNING)
logging.captureWarnings(True)
show = partial(show, progress=None, reset_camera=Camera.KEEP)
# ---------------------------------------------------------

cover = Cover(cols=6)
switch = PowerSwitch()
button = Button()

cover.export_stl("cover.stl")
button.export_stl("button.stl")
switch.export_stl("switch.stl")

cover.joints["switch_slide"].connect_to(switch.joints["joint"])
cover.joints["button"].connect_to(button.joints["joint"])

show(cover, switch, button)

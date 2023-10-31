import logging
import os

from build123d import *
from ocp_vscode import show, Camera
from OCP import Message  # Make things less verbose

from cover import Cover
from switch import PowerSwitch
from button import Button
from bottom import BottomPlate
from mc_cover import MCCover


# --| Boilerplate |----------------------------------------
for printer in Message.Message.DefaultMessenger_s().Printers():
    printer.SetTraceLevel(Message.Message_Gravity(3))
log = logging.getLogger(__name__)
logging.getLogger("build123d").setLevel(logging.WARNING)
logging.captureWarnings(True)
# ---------------------------------------------------------

COLS=6

cover = Cover(cols=COLS)
switch = PowerSwitch()
button = Button()
bottom = BottomPlate(cols=COLS)
mc_cover = MCCover()

cover.joints["switch_slide"].connect_to(switch.joints["joint"])
cover.joints["button"].connect_to(button.joints["joint"])
cover.joints["bottom"].connect_to(bottom.joints["joint"])

assembly = Compound(
    label="Corne Wireless Case",
    children=[cover, switch, button, bottom]
)

for part in assembly.children:
    part.color = Color(0, 0, 0)

assembly = Rotation(about_y=180) * Pos(10, 0, 0) * assembly

show(assembly, progress=None, reset_camera=Camera.KEEP)

# Export step & stl files
for part in assembly.children:
    if not os.path.exists("step"):
        os.mkdir("step")
    if not os.path.exists("stl"):
        os.mkdir("stl")

    part.export_stl(os.path.join("stl", f"{part.label}.stl"))
    part.export_step(os.path.join("stl", f"{part.label}.step"))

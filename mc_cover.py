from build123d import *
from ocp_vscode import show, Camera

C, MIN, MAX = Align.CENTER, Align.MIN, Align.MAX


class MCCover(Part):
    def __init__(self, **kwargs):
        kwargs["label"] = kwargs.get("label", "MC/display cover")
        part = Part()
        super().__init__(part.wrapped, **kwargs)

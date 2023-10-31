from build123d import *

from cover import HULL_THICKNESS

C, MIN, MAX = Align.CENTER, Align.MIN, Align.MAX


class Button(Part):
    def __init__(self, **kwargs):
        tol_z = .1
        tol_xy = .3
        kwargs["label"] = kwargs.get("label", "Reset button")
        button = Box(2.7 - tol_xy, 0.3 + HULL_THICKNESS * 0.70 - tol_xy, 2.7 - tol_z, align=(C, MIN, MIN))
        button += Box(4.7 - tol_xy, 0.3 + HULL_THICKNESS * 0.30, 4.8 - tol_z, align=(C, MAX, MIN))

        joint_location = Location(Plane.XZ)
        joint = RigidJoint("joint", button, joint_location=joint_location)

        super().__init__(button.wrapped, joints={"joint": joint}, **kwargs)

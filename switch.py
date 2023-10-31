from build123d import *

from cover import HULL_THICKNESS

C, MIN, MAX = Align.CENTER, Align.MIN, Align.MAX


class PowerSwitch(Part):
    def __init__(self, **kwargs):
        kwargs["label"] = kwargs.get("label", "Power switch")
        ln = Line((0, 0), (-4, 0))
        ln += Line(ln @ 1, ln @ 1 + Vector(0, -(HULL_THICKNESS-0.5)))
        ln += Line(ln @ 1, ln @ 1 + Vector(2.75, 0))
        ln += Line(ln @ 1, ln @ 1 + Vector(0, -0.9))
        ln += Line(ln @ 1, ln @ 1 + Vector(0.85, 0))
        ln += Line(ln @ 1, ln @ 1 + Vector(0, -0.5))
        ln += Line(ln @ 1, ln @ 1 + Vector(0.4, 0))

        sk = make_face(ln + mirror(ln, about=Plane.YZ))

        switch = extrude(sk, 2.6)
        switch += Box(2.5, HULL_THICKNESS-0.5, 4.1, align=(C, MAX, MIN))
        switch -= Pos(0, 0, 0.2) * Box(1.5, 1.5, 3.9, align=(C, MAX, MIN))

        joint_location = Location(-Plane.YX, Vector(0, -(HULL_THICKNESS-0.5), 0))
        joint = RigidJoint("joint", switch, joint_location=joint_location)

        super().__init__(switch.wrapped, joints={"joint": joint}, **kwargs)

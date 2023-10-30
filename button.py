from build123d import *

C, MIN, MAX = Align.CENTER, Align.MIN, Align.MAX


class Button(Part):
    def __init__(self):
        button = Box(2.7, 0.9, 2.7, align=(C, MIN, MIN))
        button += Box(4.7, 1.5, 5.4, align=(C, MAX, MIN))

        joint_location = Location(Plane.XZ)
        joint = RigidJoint("joint", button, joint_location=joint_location)

        super().__init__(button.wrapped, joints={"joint": joint})

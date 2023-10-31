from build123d import *

from corne_board import BasePlateLine, ScrewLocations

C, MIN, MAX = Align.CENTER, Align.MIN, Align.MAX


class BottomPlate(Part):
    def __init__(self, cols=6, **kwargs):
        kwargs["label"] = kwargs.get("label", "MC/display cover")
        sk = make_face(BasePlateLine(cols=cols))
        part = extrude(sk, 1.3)

        # Add threaded inserts
        top_face = part.faces().sort_by(Axis.Z).last
        plane = Plane((0, 0, top_face.center().Z))
        part += plane * ScrewLocations(cols=cols) * Cylinder(3, 1.5)
        part -= plane * ScrewLocations(cols=cols) * Cylinder(2, 1.5)

        # Add feet pads insets
        radius = 4.5
        offset = radius + 3  #  pad distance from corner
        bottom_face = part.faces().sort_by(Axis.Z).first
        edges = bottom_face.edges().sort_by(Axis.X)
        corners = (edges.first + edges.last).vertices()
        z = corners[0].Z

        inset = Cylinder(radius, .5, align=(C, C, MIN))

        part -= Pos(corners[0].X + offset, corners[0].Y + offset, z) * inset
        part -= Pos(corners[1].X + offset, corners[1].Y - offset, z) * inset
        part -= Pos(corners[2].X - offset, corners[2].Y - offset, z) * inset
        part -= Pos(corners[3].X - offset, corners[3].Y + offset, z) * inset

        # Add a fifth foot for stability
        corner = bottom_face.vertices().sort_by(Axis.Y).first
        part -= Pos(corner.X + 2, corner.Y + offset + 2, z) * inset

        # mirror 180°
        part = mirror(part, about=Plane.YZ)

        # Add connection point for cover
        joint = RigidJoint("joint", part, joint_location=Location(Plane.XY))

        super().__init__(part.wrapped, joints={"joint": joint}, **kwargs)

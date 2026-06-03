import math
import traceback

import adsk.core
import adsk.fusion


# Fusion internal distance unit is cm. All input parameters below are mm.
PARAMS = {
    "base_X": 40.0,
    "base_Y": 42.4,
    "plate_T": 3.0,
    "base_corner_R": 3.0,
    "bend_outer_R": 2.0,
    "base_hole_D": 4.0,
    "base_hole_pitch_X": 30.0,
    "base_hole_pitch_Y": 23.4,
    "base_hole_front_offset_Y": 8.0,
    "motor_face_outer_Y": 42.4,
    "motor_face_X": 40.0,
    "motor_face_H": 47.0,
    "motor_face_bottom_Z": 3.0,
    "motor_face_arc_center_Z": 27.0,
    "motor_axis_Z": 26.5,
    "motor_slot_W": 13.0,
    "motor_slot_H": 27.0,
    "motor_hole_D": 3.2,
    "motor_hole_pcd": 31.0,
}


def mm(value):
    return value / 10.0


def point_xy(x, y, z=0.0):
    return adsk.core.Point3D.create(mm(x), mm(y), mm(z))


def point_xz(x, z, y=0.0):
    return adsk.core.Point3D.create(mm(x), mm(y), mm(z))


def create_offset_plane(root, base_plane, offset_mm):
    planes = root.constructionPlanes
    plane_input = planes.createInput()
    plane_input.setByOffset(base_plane, adsk.core.ValueInput.createByReal(mm(offset_mm)))
    return planes.add(plane_input)


def first_profile(sketch, label):
    if sketch.profiles.count < 1:
        raise RuntimeError("No closed profile was created for {}.".format(label))
    return sketch.profiles.item(0)


def largest_profile(sketch, label):
    if sketch.profiles.count < 1:
        raise RuntimeError("No closed profile was created for {}.".format(label))

    largest = sketch.profiles.item(0)
    largest_area = -1.0
    for index in range(sketch.profiles.count):
        profile = sketch.profiles.item(index)
        try:
            area = profile.areaProperties(adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy).area
        except Exception:
            area = profile.boundingBox.maxPoint.distanceTo(profile.boundingBox.minPoint)
        if area > largest_area:
            largest = profile
            largest_area = area
    return largest


def all_profiles(sketch, label):
    if sketch.profiles.count < 1:
        raise RuntimeError("No closed profiles were created for {}.".format(label))
    profiles = adsk.core.ObjectCollection.create()
    for index in range(sketch.profiles.count):
        profiles.add(sketch.profiles.item(index))
    return profiles


def extrude_profiles(root, profiles, distance_mm, operation):
    if not isinstance(profiles, adsk.core.ObjectCollection):
        obj = adsk.core.ObjectCollection.create()
        for profile in profiles:
            obj.add(profile)
        profiles = obj

    extrudes = root.features.extrudeFeatures
    ext_input = extrudes.createInput(profiles, operation)
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(distance_mm)))
    return extrudes.add(ext_input)


def add_rounded_rect(sketch, x0, y0, x1, y1, radius):
    lines = sketch.sketchCurves.sketchLines
    arcs = sketch.sketchCurves.sketchArcs
    r = min(radius, abs(x1 - x0) / 2.0, abs(y1 - y0) / 2.0)
    k = r / math.sqrt(2.0)

    lines.addByTwoPoints(point_xy(x0 + r, y0), point_xy(x1 - r, y0))
    arcs.addByThreePoints(point_xy(x1 - r, y0), point_xy(x1 - r + k, y0 + r - k), point_xy(x1, y0 + r))
    lines.addByTwoPoints(point_xy(x1, y0 + r), point_xy(x1, y1 - r))
    arcs.addByThreePoints(point_xy(x1, y1 - r), point_xy(x1 - r + k, y1 - r + k), point_xy(x1 - r, y1))
    lines.addByTwoPoints(point_xy(x1 - r, y1), point_xy(x0 + r, y1))
    arcs.addByThreePoints(point_xy(x0 + r, y1), point_xy(x0 + r - k, y1 - r + k), point_xy(x0, y1 - r))
    lines.addByTwoPoints(point_xy(x0, y1 - r), point_xy(x0, y0 + r))
    arcs.addByThreePoints(point_xy(x0, y0 + r), point_xy(x0 + r - k, y0 + r - k), point_xy(x0 + r, y0))


def add_motor_face_outline(sketch, p):
    half_w = p["motor_face_X"] / 2.0
    bottom_z = p["motor_face_bottom_Z"]
    arc_center_z = p["motor_face_arc_center_Z"]
    top_z = p["motor_face_H"]

    lines = sketch.sketchCurves.sketchLines
    arcs = sketch.sketchCurves.sketchArcs

    lines.addByTwoPoints(point_xz(-half_w, bottom_z), point_xz(half_w, bottom_z))
    lines.addByTwoPoints(point_xz(half_w, bottom_z), point_xz(half_w, arc_center_z))
    arcs.addByThreePoints(point_xz(half_w, arc_center_z), point_xz(0.0, top_z), point_xz(-half_w, arc_center_z))
    lines.addByTwoPoints(point_xz(-half_w, arc_center_z), point_xz(-half_w, bottom_z))


def add_vertical_slot(sketch, cx, cz, width, height, plane_y=0.0):
    curves = sketch.sketchCurves
    lines = curves.sketchLines
    arcs = curves.sketchArcs
    radius = width / 2.0
    top_center_z = cz + height / 2.0 - radius
    bottom_center_z = cz - height / 2.0 + radius
    left_x = cx - radius
    right_x = cx + radius

    lines.addByTwoPoints(point_xz(left_x, bottom_center_z, plane_y), point_xz(left_x, top_center_z, plane_y))
    arcs.addByThreePoints(
        point_xz(left_x, top_center_z, plane_y),
        point_xz(cx, top_center_z + radius, plane_y),
        point_xz(right_x, top_center_z, plane_y),
    )
    lines.addByTwoPoints(point_xz(right_x, top_center_z, plane_y), point_xz(right_x, bottom_center_z, plane_y))
    arcs.addByThreePoints(
        point_xz(right_x, bottom_center_z, plane_y),
        point_xz(cx, bottom_center_z - radius, plane_y),
        point_xz(left_x, bottom_center_z, plane_y),
    )


def add_motor_face_cutout_loops(sketch, p, plane_y):
    add_vertical_slot(sketch, 0.0, p["motor_axis_Z"], p["motor_slot_W"], p["motor_slot_H"], plane_y)

    hole_radius = p["motor_hole_D"] / 2.0
    pcd_radius = p["motor_hole_pcd"] / 2.0
    for deg in (0, 60, 120, 180, 240, 300):
        rad = math.radians(deg)
        x = math.cos(rad) * pcd_radius
        z = p["motor_axis_Z"] + math.sin(rad) * pcd_radius
        sketch.sketchCurves.sketchCircles.addByCenterRadius(point_xz(x, z, plane_y), mm(hole_radius))


def create_base_plate(root, xy_plane, p):
    sketch = root.sketches.add(xy_plane)
    add_rounded_rect(
        sketch,
        -p["base_X"] / 2.0,
        0.0,
        p["base_X"] / 2.0,
        p["base_Y"],
        p["base_corner_R"],
    )
    feature = extrude_profiles(
        root,
        [first_profile(sketch, "bracket chassis mounting face")],
        p["plate_T"],
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = feature.bodies.item(0)
    body.name = "jgb37_bracket_integral_l_shape"
    return body


def create_motor_face(root, xz_plane, p):
    plane_y = p["motor_face_outer_Y"]
    sketch_plane = create_offset_plane(root, xz_plane, plane_y)
    sketch = root.sketches.add(sketch_plane)
    add_motor_face_outline(sketch, p)
    add_motor_face_cutout_loops(sketch, p, plane_y)
    extrude_profiles(
        root,
        [largest_profile(sketch, "bracket motor mounting face with cutouts")],
        -p["plate_T"],
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
    )


def cut_base_holes(root, xy_plane, p):
    plane_z = -0.2
    sketch_plane = create_offset_plane(root, xy_plane, plane_z)
    sketch = root.sketches.add(sketch_plane)
    hole_radius = p["base_hole_D"] / 2.0
    x_values = (-p["base_hole_pitch_X"] / 2.0, p["base_hole_pitch_X"] / 2.0)
    y0 = p["base_hole_front_offset_Y"]
    y_values = (y0, y0 + p["base_hole_pitch_Y"])
    for x in x_values:
        for y in y_values:
            sketch.sketchCurves.sketchCircles.addByCenterRadius(point_xy(x, y, plane_z), mm(hole_radius))
    extrude_profiles(
        root,
        all_profiles(sketch, "base mounting holes"),
        p["plate_T"] + 0.4,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
    )


def add_outer_bend_fillet(root, p):
    target = None
    tolerance = mm(0.08)
    target_y = mm(p["motor_face_outer_Y"] - p["plate_T"])
    target_z = mm(p["plate_T"])

    for body in root.bRepBodies:
        if "jgb37_bracket" not in body.name:
            continue
        for edge in body.edges:
            box = edge.boundingBox
            spans_width = box.minPoint.x < mm(-p["base_X"] / 2.0 + 0.5) and box.maxPoint.x > mm(p["base_X"] / 2.0 - 0.5)
            near_y = abs(box.minPoint.y - target_y) < tolerance and abs(box.maxPoint.y - target_y) < tolerance
            near_z = abs(box.minPoint.z - target_z) < tolerance and abs(box.maxPoint.z - target_z) < tolerance
            if spans_width and near_y and near_z:
                target = edge
                break
        if target:
            break

    if not target:
        return False

    edge_collection = adsk.core.ObjectCollection.create()
    edge_collection.add(target)
    fillet_input = root.features.filletFeatures.createInput()
    fillet_input.addConstantRadiusEdgeSet(
        edge_collection,
        adsk.core.ValueInput.createByReal(mm(p["bend_outer_R"])),
        True,
    )
    try:
        root.features.filletFeatures.add(fillet_input)
        return True
    except Exception:
        return False


def assign_bracket_appearance(design, root):
    try:
        appearance = design.appearances.itemByName("Steel - Satin")
        if not appearance:
            appearance = design.appearances.itemByName("Steel - Brushed")
        if appearance:
            for body in root.bRepBodies:
                if "jgb37_bracket" in body.name:
                    body.appearance = appearance
    except Exception:
        pass


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = app.activeProduct
        if not isinstance(design, adsk.fusion.Design):
            ui.messageBox("Please switch to the Fusion Design workspace first.")
            return

        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        p = PARAMS

        create_base_plate(root, root.xYConstructionPlane, p)
        create_motor_face(root, root.xZConstructionPlane, p)
        fillet_ok = add_outer_bend_fillet(root, p)
        cut_base_holes(root, root.xYConstructionPlane, p)
        assign_bracket_appearance(design, root)

        ui.messageBox(
            "JGB37 motor bracket v0.1 rebuilt.\n\n"
            "Chassis mounting face: %.1f x %.1f x %.1f mm, R%.1f corners\n"
            "Motor mounting face: %.1f mm wide, %.1f mm total height, rectangle + semicircular top\n"
            "Base holes: 4 x D%.1f, pitch %.1f x %.1f mm\n"
            "Motor face: slot %.1f x %.1f mm, 6 x D%.1f on D%.1f PCD\n"
            "Outer L-bend fillet: %s"
            % (
                p["base_X"],
                p["base_Y"],
                p["plate_T"],
                p["base_corner_R"],
                p["motor_face_X"],
                p["motor_face_H"],
                p["base_hole_D"],
                p["base_hole_pitch_X"],
                p["base_hole_pitch_Y"],
                p["motor_slot_W"],
                p["motor_slot_H"],
                p["motor_hole_D"],
                p["motor_hole_pcd"],
                "R%.1f mm" % p["bend_outer_R"] if fillet_ok else "not applied automatically",
            )
        )

    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

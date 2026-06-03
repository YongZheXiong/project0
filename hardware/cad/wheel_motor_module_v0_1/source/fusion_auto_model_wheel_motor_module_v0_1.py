import math
import traceback

import adsk.core
import adsk.fusion


# Fusion internal distance unit is cm. All input parameters below are mm.
PARAMS = {
    "track_width": 173.0,
    "wheel_D": 85.0,
    "wheel_W": 33.4,
    "wheel_hub_D": 57.6,
    "wheel_coupler_total_W": 36.04,
    "coupler_D": 20.0,
    "coupler_L": 11.8,
    "motor_D": 37.0,
    "motor_encoder_D": 32.3,
    "motor_gearbox_L": 24.0,
    "motor_body_L": 26.0,
    "motor_encoder_L": 22.0,
    "motor_shaft_D": 6.0,
    "motor_shaft_L": 15.0,
    "bracket_chassis_face_X": 40.0,
    "bracket_chassis_face_Y": 42.4,
    "bracket_chassis_face_T": 3.0,
    "bracket_motor_face_X": 40.0,
    "bracket_motor_face_H": 47.0,
    "bracket_motor_face_T": 3.0,
    "bracket_hole_D": 4.0,
    "bracket_hole_pitch_X": 30.0,
    "bracket_hole_pitch_Y": 23.4,
    "bracket_base_hole_edge_y": 8.0,
    "bracket_motor_hole_D": 3.2,
    "bracket_motor_hole_pcd": 31.0,
    "bracket_motor_slot_W": 13.0,
    "bracket_motor_slot_H": 27.0,
    "axis_to_chassis_face_inner": 33.0,
    "wheel_inner_to_motor_face_outer": 8.8,
    "single_module_x": -115.0,
    "pair_module_x": 85.0,
    "axis_marker_L": 112.0,
}


def mm(value):
    return value / 10.0


def point(x, y, z=0.0):
    return adsk.core.Point3D.create(mm(x), mm(y), mm(z))


def add_center_rect(sketch, cx, cy, lx, ly):
    lines = sketch.sketchCurves.sketchLines
    p0 = point(cx - lx / 2.0, cy - ly / 2.0)
    p1 = point(cx + lx / 2.0, cy - ly / 2.0)
    p2 = point(cx + lx / 2.0, cy + ly / 2.0)
    p3 = point(cx - lx / 2.0, cy + ly / 2.0)
    lines.addByTwoPoints(p0, p1)
    lines.addByTwoPoints(p1, p2)
    lines.addByTwoPoints(p2, p3)
    lines.addByTwoPoints(p3, p0)


def extrude_profiles(root, profiles, distance_mm, operation):
    extrudes = root.features.extrudeFeatures
    obj = adsk.core.ObjectCollection.create()
    for profile in profiles:
        obj.add(profile)
    ext_input = extrudes.createInput(obj, operation)
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(distance_mm)))
    return extrudes.add(ext_input)


def first_profile(sketch, label):
    if sketch.profiles.count < 1:
        raise RuntimeError("No closed profile was created for {}.".format(label))
    return sketch.profiles.item(0)


def create_offset_plane(root, base_plane, offset_mm):
    planes = root.constructionPlanes
    plane_input = planes.createInput()
    plane_input.setByOffset(base_plane, adsk.core.ValueInput.createByReal(mm(offset_mm)))
    return planes.add(plane_input)


def create_box_xy_op(root, xy_plane, cx, cy, lx, ly, z_bottom, height, name, operation):
    plane = create_offset_plane(root, xy_plane, z_bottom)
    sketch = root.sketches.add(plane)
    add_center_rect(sketch, cx, cy, lx, ly)
    feature = extrude_profiles(
        root,
        [first_profile(sketch, name)],
        height,
        operation,
    )
    if feature.bodies.count > 0:
        body = feature.bodies.item(0)
        body.name = name
        return body
    return None


def create_box_xy(root, xy_plane, cx, cy, lx, ly, z_bottom, height, name):
    return create_box_xy_op(
        root,
        xy_plane,
        cx,
        cy,
        lx,
        ly,
        z_bottom,
        height,
        name,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )


def create_box_yz(root, yz_plane, x_center, cy, cz, ly, lz, thickness_x, name):
    plane = create_offset_plane(root, yz_plane, x_center - thickness_x / 2.0)
    sketch = root.sketches.add(plane)
    add_center_rect(sketch, cy, cz, ly, lz)
    feature = extrude_profiles(
        root,
        [first_profile(sketch, name)],
        thickness_x,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = feature.bodies.item(0)
    body.name = name
    return body


def create_cylinder_z(root, xy_plane, cx, cy, z_bottom, diameter, height, name):
    plane = create_offset_plane(root, xy_plane, z_bottom)
    sketch = root.sketches.add(plane)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(point(cx, cy), mm(diameter / 2.0))
    feature = extrude_profiles(
        root,
        [first_profile(sketch, name)],
        height,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = feature.bodies.item(0)
    body.name = name
    return body


def cut_circles_on_xy(root, xy_plane, centers, diameter, z_start, depth, name):
    plane = create_offset_plane(root, xy_plane, z_start)
    sketch = root.sketches.add(plane)
    for cx, cy in centers:
        sketch.sketchCurves.sketchCircles.addByCenterRadius(point(cx, cy), mm(diameter / 2.0))
    profiles = [sketch.profiles.item(i) for i in range(sketch.profiles.count)]
    if not profiles:
        raise RuntimeError("No cut profiles were created for {}.".format(name))
    return extrude_profiles(root, profiles, depth, adsk.fusion.FeatureOperations.CutFeatureOperation)


def add_slot_xz(sketch, cx, cz, width_x, height_z):
    curves = sketch.sketchCurves
    lines = curves.sketchLines
    arcs = curves.sketchArcs
    r = width_x / 2.0
    top_z = cz + height_z / 2.0 - r
    bottom_z = cz - height_z / 2.0 + r
    left_x = cx - r
    right_x = cx + r

    p_top_l = point(left_x, top_z)
    p_top_r = point(right_x, top_z)
    p_bot_l = point(left_x, bottom_z)
    p_bot_r = point(right_x, bottom_z)
    lines.addByTwoPoints(p_top_l, p_bot_l)
    arcs.addByCenterStartSweep(point(cx, bottom_z), p_bot_l, math.pi)
    lines.addByTwoPoints(p_bot_r, p_top_r)
    arcs.addByCenterStartSweep(point(cx, top_z), p_top_r, math.pi)


def create_motor_face_feature_markers(root, xy_plane, x_center, side, p, d, name):
    motor_face_outer_y = signed_y(d["motor_face_outer_abs"], side)
    axis_z = d["axis_z"]
    marker_y = motor_face_outer_y + side * 0.35

    create_box_xy(
        root,
        xy_plane,
        x_center,
        marker_y,
        p["bracket_motor_slot_W"],
        0.7,
        axis_z - p["bracket_motor_slot_H"] / 2.0,
        p["bracket_motor_slot_H"],
        "{}_slot_marker_13x27_not_cut".format(name),
    )

    r = p["bracket_motor_hole_pcd"] / 2.0
    for deg in (30, 90, 150, 210, 270, 330):
        rad = math.radians(deg)
        cx = x_center + math.cos(rad) * r
        cz = axis_z + math.sin(rad) * r
        create_cylinder_y(
            root,
            xy_plane,
            cx,
            marker_y,
            cz,
            p["bracket_motor_hole_D"],
            0.8,
            "{}_hole_marker_{:03d}_not_cut".format(name, deg),
        )


def body_center(body):
    box = body.boundingBox
    return adsk.core.Point3D.create(
        (box.minPoint.x + box.maxPoint.x) / 2.0,
        (box.minPoint.y + box.maxPoint.y) / 2.0,
        (box.minPoint.z + box.maxPoint.z) / 2.0,
    )


def move_body(root, body, matrix):
    bodies = adsk.core.ObjectCollection.create()
    bodies.add(body)
    move_features = root.features.moveFeatures
    move_input = move_features.createInput(bodies, matrix)
    return move_features.add(move_input)


def create_cylinder_y(root, xy_plane, cx, cy, cz, diameter, length, name):
    body = create_cylinder_z(root, xy_plane, cx, cy, cz - length / 2.0, diameter, length, name)
    transform = adsk.core.Matrix3D.create()
    transform.setToRotation(math.pi / 2.0, adsk.core.Vector3D.create(1.0, 0.0, 0.0), body_center(body))
    move_body(root, body, transform)
    return body


def create_axis_marker(root, xy_plane, cx, cy, cz, length, name):
    return create_cylinder_y(root, xy_plane, cx, cy, cz, 1.2, length, name)


def derived(p):
    motor_axial_L = p["motor_gearbox_L"] + p["motor_body_L"] + p["motor_encoder_L"]
    chassis_face_inner_z = -p["bracket_chassis_face_T"]
    axis_z = chassis_face_inner_z - p["axis_to_chassis_face_inner"]
    ground_z = axis_z - p["wheel_D"] / 2.0
    motor_top_clearance = p["axis_to_chassis_face_inner"] - p["motor_D"] / 2.0
    side_inner_abs = p["track_width"] / 2.0 - p["wheel_coupler_total_W"] / 2.0
    motor_face_outer_abs = side_inner_abs - p["wheel_inner_to_motor_face_outer"]
    motor_face_inner_abs = motor_face_outer_abs - p["bracket_motor_face_T"]
    motor_inner_end_abs = motor_face_inner_abs - motor_axial_L
    center_gap = 2.0 * motor_inner_end_abs
    required_track_no_overlap = 2.0 * (
        p["wheel_coupler_total_W"] / 2.0
        + p["wheel_inner_to_motor_face_outer"]
        + p["bracket_motor_face_T"]
        + motor_axial_L
    )
    return {
        "motor_axial_L": motor_axial_L,
        "chassis_face_inner_z": chassis_face_inner_z,
        "axis_z": axis_z,
        "ground_z": ground_z,
        "motor_top_clearance": motor_top_clearance,
        "side_inner_abs": side_inner_abs,
        "motor_face_outer_abs": motor_face_outer_abs,
        "motor_face_inner_abs": motor_face_inner_abs,
        "motor_inner_end_abs": motor_inner_end_abs,
        "center_gap": center_gap,
        "required_track_no_overlap": required_track_no_overlap,
    }


def signed_y(abs_y, side):
    return side * abs_y


def create_motor_bracket(root, xy_plane, cx, side, p, d, label):
    base_center_y = signed_y((d["motor_face_outer_abs"] + d["motor_face_inner_abs"]) / 2.0, side)
    create_box_xy_op(
        root,
        xy_plane,
        cx,
        base_center_y,
        p["bracket_chassis_face_X"],
        p["bracket_chassis_face_Y"],
        -p["bracket_chassis_face_T"],
        p["bracket_chassis_face_T"],
        "{}_bracket_chassis_mount_face_integral".format(label),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )

    motor_face_center_y = signed_y(
        d["motor_face_outer_abs"] - p["bracket_motor_face_T"] / 2.0,
        side,
    )
    create_box_xy_op(
        root,
        xy_plane,
        cx,
        motor_face_center_y,
        p["bracket_motor_face_X"],
        p["bracket_motor_face_T"],
        -p["bracket_chassis_face_T"] - p["bracket_motor_face_H"],
        p["bracket_motor_face_H"],
        "{}_bracket_motor_mount_face_integral".format(label),
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
    )

    base_hole_centers = []
    for dx in (-p["bracket_hole_pitch_X"] / 2.0, p["bracket_hole_pitch_X"] / 2.0):
        for dy in (-p["bracket_hole_pitch_Y"] / 2.0, p["bracket_hole_pitch_Y"] / 2.0):
            base_hole_centers.append((cx + dx, base_center_y + side * dy))
    cut_circles_on_xy(
        root,
        xy_plane,
        base_hole_centers,
        p["bracket_hole_D"],
        0.2,
        -p["bracket_chassis_face_T"] - 0.4,
        "{}_bracket_base_holes".format(label),
    )
    create_motor_face_feature_markers(root, xy_plane, cx, side, p, d, "{}_bracket_motor_face_features".format(label))


def create_wheel_motor_side(root, xy_plane, cx, side, p, d, label):
    axis_z = d["axis_z"]
    wheel_y = signed_y(p["track_width"] / 2.0, side)
    create_cylinder_y(
        root,
        xy_plane,
        cx,
        wheel_y,
        axis_z,
        p["wheel_D"],
        p["wheel_W"],
        "{}_wheel_D85_W33_4".format(label),
    )
    create_cylinder_y(
        root,
        xy_plane,
        cx,
        wheel_y,
        axis_z,
        p["wheel_hub_D"],
        p["wheel_W"] + 0.6,
        "{}_wheel_hub_reference_D57_6".format(label),
    )

    coupler_y = signed_y(d["side_inner_abs"] - p["coupler_L"] / 2.0, side)
    create_cylinder_y(
        root,
        xy_plane,
        cx,
        coupler_y,
        axis_z,
        p["coupler_D"],
        p["coupler_L"],
        "{}_coupler_D20_L11_8".format(label),
    )

    shaft_y = signed_y(d["motor_face_outer_abs"] + p["motor_shaft_L"] / 2.0, side)
    create_cylinder_y(
        root,
        xy_plane,
        cx,
        shaft_y,
        axis_z,
        p["motor_shaft_D"],
        p["motor_shaft_L"],
        "{}_motor_output_shaft_D6_L15_reference".format(label),
    )

    inward = -side
    motor_face_inner_y = signed_y(d["motor_face_inner_abs"], side)
    gearbox_y = motor_face_inner_y + inward * p["motor_gearbox_L"] / 2.0
    create_cylinder_y(
        root,
        xy_plane,
        cx,
        gearbox_y,
        axis_z,
        p["motor_D"],
        p["motor_gearbox_L"],
        "{}_motor_gearbox_D37_L24".format(label),
    )

    body_y = motor_face_inner_y + inward * (p["motor_gearbox_L"] + p["motor_body_L"] / 2.0)
    create_cylinder_y(
        root,
        xy_plane,
        cx,
        body_y,
        axis_z,
        p["motor_D"],
        p["motor_body_L"],
        "{}_motor_body_D37_L26_simplified".format(label),
    )

    encoder_y = motor_face_inner_y + inward * (
        p["motor_gearbox_L"] + p["motor_body_L"] + p["motor_encoder_L"] / 2.0
    )
    create_cylinder_y(
        root,
        xy_plane,
        cx,
        encoder_y,
        axis_z,
        p["motor_encoder_D"],
        p["motor_encoder_L"],
        "{}_motor_encoder_D32_3_L22_simplified".format(label),
    )

    create_motor_bracket(root, xy_plane, cx, side, p, d, label)
    create_axis_marker(root, xy_plane, cx, signed_y(43.0, side), axis_z, p["axis_marker_L"], "{}_axis_marker".format(label))


def create_ground_reference(root, xy_plane, cx, p, d, label):
    create_box_xy(
        root,
        xy_plane,
        cx,
        0.0,
        58.0,
        p["track_width"] + 34.0,
        d["ground_z"] - 0.6,
        0.6,
        "{}_ground_reference_wheel_bottom".format(label),
    )


def assign_body_appearance(design, body, appearance_name):
    try:
        appearance = design.appearances.itemByName(appearance_name)
        if appearance:
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
        xy = root.xYConstructionPlane
        p = PARAMS
        d = derived(p)

        create_ground_reference(root, xy, p["single_module_x"], p, d, "single_left")
        create_wheel_motor_side(root, xy, p["single_module_x"], 1.0, p, d, "single_left")

        create_ground_reference(root, xy, p["pair_module_x"], p, d, "pair")
        create_wheel_motor_side(root, xy, p["pair_module_x"], 1.0, p, d, "pair_left")
        create_wheel_motor_side(root, xy, p["pair_module_x"], -1.0, p, d, "pair_right")

        for body in root.bRepBodies:
            if "wheel" in body.name:
                assign_body_appearance(design, body, "Rubber - Black")
            elif "motor" in body.name:
                assign_body_appearance(design, body, "Aluminum - Satin")
            elif "coupler" in body.name or "shaft" in body.name:
                assign_body_appearance(design, body, "Steel - Satin")
            elif "bracket" in body.name:
                assign_body_appearance(design, body, "Steel - Brushed")

        overlap_text = "NO OVERLAP" if d["center_gap"] >= 0 else "OVERLAP %.1f mm" % abs(d["center_gap"])
        ui.messageBox(
            "Wheel motor module v0.1 created.\n"
            "Left single module is at X=%.1f; mirrored pair check is at X=%.1f.\n\n"
            "Inputs:\n"
            "Track width: %.1f mm\n"
            "Wheel: D%.1f x %.1f mm\n"
            "Wheel+coupler measured total width: %.2f mm\n"
            "Wheel inner to motor-mount face outer side: %.1f mm\n"
            "Axis to chassis-mount inner face: %.1f mm\n"
            "Motor axial envelope: %.1f mm\n\n"
            "Derived:\n"
            "Chassis-mount inner face Z: %.1f mm\n"
            "Axis Z relative to chassis underside: %.1f mm\n"
            "Ground reference Z: %.1f mm\n"
            "Motor top clearance to chassis-mount inner face: %.1f mm\n"
            "Motor inner end Y abs: %.1f mm\n"
            "Center gap at current track: %.1f mm (%s)\n"
            "Required track for zero motor overlap: %.1f mm"
            % (
                p["single_module_x"],
                p["pair_module_x"],
                p["track_width"],
                p["wheel_D"],
                p["wheel_W"],
                p["wheel_coupler_total_W"],
                p["wheel_inner_to_motor_face_outer"],
                p["axis_to_chassis_face_inner"],
                d["motor_axial_L"],
                d["chassis_face_inner_z"],
                d["axis_z"],
                d["ground_z"],
                d["motor_top_clearance"],
                d["motor_inner_end_abs"],
                d["center_gap"],
                overlap_text,
                d["required_track_no_overlap"],
            )
        )

    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

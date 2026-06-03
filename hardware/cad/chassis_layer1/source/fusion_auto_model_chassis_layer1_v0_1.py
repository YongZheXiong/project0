import math
import traceback

import adsk.core
import adsk.fusion


# Fusion internal distance unit is cm. All input parameters below are mm.
PARAMS = {
    "plate_L": 270.0,
    "plate_W": 208.4,
    "plate_T": 3.0,
    "plate_outer_R": 3.0,
    "cutout_L": 70.0,
    "cutout_depth": 40.0,
    "cutout_R": 6.0,
    "wheelbase": 180.0,
    "track_width": 175.0,
    "wheel_D": 85.0,
    "wheel_W": 33.4,
    "wheel_coupler_total_W_reference": 36.04,
    "axis_to_plate_underside": 33.673,
    "coupler_D": 20.0,
    "coupler_L": 11.8,
    "motor_D": 37.0,
    "motor_gearbox_L": 24.0,
    "motor_body_L": 26.0,
    "motor_encoder_L": 22.0,
    "motor_encoder_D": 32.3,
    "bracket_foot_X": 40.0,
    "bracket_foot_Y": 42.4,
    "bracket_foot_T": 3.0,
    "bracket_motor_face_X": 40.0,
    "bracket_motor_face_H": 47.0,
    "bracket_motor_face_T": 3.0,
    "wheel_inner_to_motor_face_outer": 9.1,
    "bracket_hole_D": 4.2,
    "bracket_hole_x_offset": 15.0,
    "left_bracket_hole_y_rows": (51.6, 27.3),
    "right_bracket_hole_y_rows": (-51.6, -27.3),
    "battery_tray_X": 81.7,
    "battery_tray_Y": 139.5,
    "battery_tray_H": 18.0,
    "battery_tray_base_T": 3.0,
    "battery_tray_wall_T": 3.0,
    "battery_tray_wall_H": 15.0,
    "battery_body_X": 67.7,
    "battery_body_Y": 132.0,
    "battery_body_H": 56.0,
    "battery_mount_D": 3.2,
    "battery_mount_edge_offset": 8.0,
    "driver_X": 58.0,
    "driver_Y": 50.0,
    "driver_H_with_standoff": 17.6,
    "driver_mount_pitch_X": 45.0,
    "driver_mount_pitch_Y": 45.0,
    "driver_mount_D": 3.2,
    "fuse_X": 88.0,
    "fuse_Y": 84.2,
    "fuse_H": 36.2,
    "fuse_mount_pitch_X": 73.7,
    "fuse_mount_pitch_Y": 69.8,
    "fuse_mount_D": 4.0,
    "marker_H": 0.8,
}


LAYOUT = {
    "battery_tray": (0.0, 0.0),
    "fuse_box": (-90.0, 0.0),
    "motor_driver_front_left": (88.0, 31.5),
    "motor_driver_front_right": (88.0, -31.5),
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


def add_rounded_rect(sketch, cx, cy, lx, ly, radius):
    curves = sketch.sketchCurves
    lines = curves.sketchLines
    arcs = curves.sketchArcs

    r = min(radius, lx / 2.0 - 0.01, ly / 2.0 - 0.01)
    left = cx - lx / 2.0
    right = cx + lx / 2.0
    bottom = cy - ly / 2.0
    top = cy + ly / 2.0

    p_bl = point(left + r, bottom)
    p_br = point(right - r, bottom)
    p_rb = point(right, bottom + r)
    p_rt = point(right, top - r)
    p_tr = point(right - r, top)
    p_tl = point(left + r, top)
    p_lt = point(left, top - r)
    p_lb = point(left, bottom + r)

    lines.addByTwoPoints(p_bl, p_br)
    arcs.addByCenterStartSweep(point(right - r, bottom + r), p_br, math.pi / 2.0)
    lines.addByTwoPoints(p_rb, p_rt)
    arcs.addByCenterStartSweep(point(right - r, top - r), p_rt, math.pi / 2.0)
    lines.addByTwoPoints(p_tr, p_tl)
    arcs.addByCenterStartSweep(point(left + r, top - r), p_tl, math.pi / 2.0)
    lines.addByTwoPoints(p_lt, p_lb)
    arcs.addByCenterStartSweep(point(left + r, bottom + r), p_lb, math.pi / 2.0)


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


def create_box_xy(root, base_plane, cx, cy, lx, ly, z_bottom, height, name):
    plane = create_offset_plane(root, base_plane, z_bottom)
    sketch = root.sketches.add(plane)
    add_center_rect(sketch, cx, cy, lx, ly)
    feature = extrude_profiles(
        root,
        [first_profile(sketch, name)],
        height,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = feature.bodies.item(0)
    body.name = name
    return body


def create_cylinder_z(root, base_plane, cx, cy, z_bottom, diameter, height, name):
    plane = create_offset_plane(root, base_plane, z_bottom)
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
    axis = adsk.core.Vector3D.create(1.0, 0.0, 0.0)
    transform.setToRotation(math.pi / 2.0, axis, body_center(body))
    move_body(root, body, transform)
    return body


def cut_round_notches(root, top_plane, p):
    half_w = p["plate_W"] / 2.0
    inset = p["cutout_depth"]
    profile_margin = 8.0
    cut_profile_depth = inset + profile_margin
    notch_centers_x = (p["wheelbase"] / 2.0, -p["wheelbase"] / 2.0)

    sketch = root.sketches.add(top_plane)
    for x in notch_centers_x:
        add_rounded_rect(
            sketch,
            x,
            half_w - inset + cut_profile_depth / 2.0,
            p["cutout_L"],
            cut_profile_depth,
            p["cutout_R"],
        )
        add_rounded_rect(
            sketch,
            x,
            -half_w + inset - cut_profile_depth / 2.0,
            p["cutout_L"],
            cut_profile_depth,
            p["cutout_R"],
        )

    profiles = [sketch.profiles.item(i) for i in range(sketch.profiles.count)]
    return extrude_profiles(root, profiles, -p["plate_T"] - 0.5, adsk.fusion.FeatureOperations.CutFeatureOperation)


def cut_bracket_mount_holes(root, top_plane, p):
    xs = []
    for axle_x in (p["wheelbase"] / 2.0, -p["wheelbase"] / 2.0):
        xs.extend([axle_x - p["bracket_hole_x_offset"], axle_x + p["bracket_hole_x_offset"]])

    sketch = root.sketches.add(top_plane)
    for x in xs:
        for y in p["left_bracket_hole_y_rows"]:
            sketch.sketchCurves.sketchCircles.addByCenterRadius(point(x, y), mm(p["bracket_hole_D"] / 2.0))
        for y in p["right_bracket_hole_y_rows"]:
            sketch.sketchCurves.sketchCircles.addByCenterRadius(point(x, y), mm(p["bracket_hole_D"] / 2.0))

    profiles = [sketch.profiles.item(i) for i in range(sketch.profiles.count)]
    return extrude_profiles(root, profiles, -p["plate_T"] - 0.5, adsk.fusion.FeatureOperations.CutFeatureOperation)


def add_mount_markers(root, xy_plane, cx, cy, pitch_x, pitch_y, diameter, z_bottom, label):
    for dx in (-pitch_x / 2.0, pitch_x / 2.0):
        for dy in (-pitch_y / 2.0, pitch_y / 2.0):
            create_cylinder_z(
                root,
                xy_plane,
                cx + dx,
                cy + dy,
                z_bottom,
                diameter,
                PARAMS["marker_H"],
                "{}_mount_marker".format(label),
            )


def assign_body_appearance(design, body, appearance_name):
    # Appearance names vary by Fusion installation language/version, so keep this optional.
    try:
        appearance = design.appearances.itemByName(appearance_name)
        if appearance:
            body.appearance = appearance
    except Exception:
        pass


def create_base_plate(root, xy_plane, p):
    sketch = root.sketches.add(xy_plane)
    add_rounded_rect(sketch, 0.0, 0.0, p["plate_L"], p["plate_W"], p["plate_outer_R"])
    feature = extrude_profiles(
        root,
        [first_profile(sketch, "base plate outer contour")],
        p["plate_T"],
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = feature.bodies.item(0)
    body.name = "chassis_layer1_base_plate_v0_1"
    return body


def bracket_motor_face_outer_y(p, y_sign):
    wheel_inner_abs = p["track_width"] / 2.0 - p["wheel_W"] / 2.0
    return y_sign * (wheel_inner_abs - p["wheel_inner_to_motor_face_outer"])


def bracket_motor_face_inner_y(p, y_sign):
    return bracket_motor_face_outer_y(p, y_sign) - y_sign * p["bracket_motor_face_T"]


def axle_z(p):
    return -p["axis_to_plate_underside"]


def create_wheel_modules(root, xy_plane, p):
    axis_z = axle_z(p)
    half_track = p["track_width"] / 2.0
    wheel_xs = (p["wheelbase"] / 2.0, -p["wheelbase"] / 2.0)

    for x in wheel_xs:
        for side_name, y_sign in (("left", 1.0), ("right", -1.0)):
            wheel_y = y_sign * half_track
            create_cylinder_y(
                root,
                xy_plane,
                x,
                wheel_y,
                axis_z,
                p["wheel_D"],
                p["wheel_W"],
                "wheel_envelope_{}_x_{:+.0f}".format(side_name, x),
            )

            motor_face_outer_y = bracket_motor_face_outer_y(p, y_sign)
            coupler_y = motor_face_outer_y + y_sign * p["coupler_L"] / 2.0
            create_cylinder_y(
                root,
                xy_plane,
                x,
                coupler_y,
                axis_z,
                p["coupler_D"],
                p["coupler_L"],
                "coupler_placeholder_{}_x_{:+.0f}".format(side_name, x),
            )

            motor_face_inner_y = bracket_motor_face_inner_y(p, y_sign)
            inward = -y_sign
            gearbox_y = motor_face_inner_y + inward * p["motor_gearbox_L"] / 2.0
            create_cylinder_y(
                root,
                xy_plane,
                x,
                gearbox_y,
                axis_z,
                p["motor_D"],
                p["motor_gearbox_L"],
                "motor_gearbox_placeholder_{}_x_{:+.0f}".format(side_name, x),
            )

            motor_body_y = motor_face_inner_y + inward * (p["motor_gearbox_L"] + p["motor_body_L"] / 2.0)
            create_cylinder_y(
                root,
                xy_plane,
                x,
                motor_body_y,
                axis_z,
                p["motor_D"],
                p["motor_body_L"],
                "motor_body_placeholder_{}_x_{:+.0f}".format(side_name, x),
            )

            encoder_y = motor_face_inner_y + inward * (
                p["motor_gearbox_L"] + p["motor_body_L"] + p["motor_encoder_L"] / 2.0
            )
            create_cylinder_y(
                root,
                xy_plane,
                x,
                encoder_y,
                axis_z,
                p["motor_encoder_D"],
                p["motor_encoder_L"],
                "motor_encoder_placeholder_{}_x_{:+.0f}".format(side_name, x),
            )


def create_motor_brackets(root, xy_plane, p):
    for x in (p["wheelbase"] / 2.0, -p["wheelbase"] / 2.0):
        for side_name, y_sign, rows in (
            ("left", 1.0, p["left_bracket_hole_y_rows"]),
            ("right", -1.0, p["right_bracket_hole_y_rows"]),
        ):
            base_y = sum(rows) / 2.0
            create_box_xy(
                root,
                xy_plane,
                x,
                base_y,
                p["bracket_foot_X"],
                p["bracket_foot_Y"],
                -p["bracket_foot_T"],
                p["bracket_foot_T"],
                "{}_bracket_chassis_mount_face_x_{:+.0f}".format(side_name, x),
            )

            motor_face_y = bracket_motor_face_outer_y(p, y_sign) - y_sign * p["bracket_motor_face_T"] / 2.0
            create_box_xy(
                root,
                xy_plane,
                x,
                motor_face_y,
                p["bracket_motor_face_X"],
                p["bracket_motor_face_T"],
                -p["bracket_foot_T"] - p["bracket_motor_face_H"],
                p["bracket_motor_face_H"],
                "{}_bracket_motor_mount_face_x_{:+.0f}".format(side_name, x),
            )


def create_battery_tray_and_body(root, xy_plane, p):
    z0 = p["plate_T"]
    tray_x, tray_y = LAYOUT["battery_tray"]
    base_t = p["battery_tray_base_T"]
    wall_t = p["battery_tray_wall_T"]
    wall_h = p["battery_tray_wall_H"]

    create_box_xy(
        root,
        xy_plane,
        tray_x,
        tray_y,
        p["battery_tray_X"],
        p["battery_tray_Y"],
        z0,
        base_t,
        "battery_tray_base_rotated_crosswise",
    )

    wall_z = z0 + base_t
    create_box_xy(
        root,
        xy_plane,
        tray_x - p["battery_tray_X"] / 2.0 + wall_t / 2.0,
        tray_y,
        wall_t,
        p["battery_tray_Y"],
        wall_z,
        wall_h,
        "battery_tray_left_wall_crosswise",
    )
    create_box_xy(
        root,
        xy_plane,
        tray_x + p["battery_tray_X"] / 2.0 - wall_t / 2.0,
        tray_y,
        wall_t,
        p["battery_tray_Y"],
        wall_z,
        wall_h,
        "battery_tray_right_wall_crosswise",
    )
    create_box_xy(
        root,
        xy_plane,
        tray_x,
        tray_y - p["battery_tray_Y"] / 2.0 + wall_t / 2.0,
        p["battery_tray_X"],
        wall_t,
        wall_z,
        wall_h,
        "battery_tray_rear_wall_crosswise",
    )
    create_box_xy(
        root,
        xy_plane,
        tray_x,
        tray_y + p["battery_tray_Y"] / 2.0 - wall_t / 2.0,
        p["battery_tray_X"],
        wall_t,
        wall_z,
        wall_h,
        "battery_tray_front_wall_crosswise",
    )

    create_box_xy(
        root,
        xy_plane,
        tray_x,
        tray_y,
        p["battery_body_X"],
        p["battery_body_Y"],
        z0 + base_t,
        p["battery_body_H"],
        "battery_body_envelope_132x67_7x56_crosswise",
    )

    battery_pitch_x = p["battery_tray_X"] - 2.0 * p["battery_mount_edge_offset"]
    battery_pitch_y = p["battery_tray_Y"] - 2.0 * p["battery_mount_edge_offset"]
    add_mount_markers(
        root,
        xy_plane,
        tray_x,
        tray_y,
        battery_pitch_x,
        battery_pitch_y,
        p["battery_mount_D"],
        z0,
        "battery_tray",
    )


def create_core_hardware(root, xy_plane, p):
    z0 = p["plate_T"]
    create_battery_tray_and_body(root, xy_plane, p)

    fuse_x, fuse_y = LAYOUT["fuse_box"]
    create_box_xy(
        root,
        xy_plane,
        fuse_x,
        fuse_y,
        p["fuse_X"],
        p["fuse_Y"],
        z0,
        p["fuse_H"],
        "fuse_box_envelope_with_cover",
    )
    add_mount_markers(root, xy_plane, fuse_x, fuse_y, p["fuse_mount_pitch_X"], p["fuse_mount_pitch_Y"], p["fuse_mount_D"], z0, "fuse_box")

    for key in ("motor_driver_front_left", "motor_driver_front_right"):
        drv_x, drv_y = LAYOUT[key]
        create_box_xy(
            root,
            xy_plane,
            drv_x,
            drv_y,
            p["driver_X"],
            p["driver_Y"],
            z0,
            p["driver_H_with_standoff"],
            "{}_envelope_with_6mm_standoff".format(key),
        )
        add_mount_markers(
            root,
            xy_plane,
            drv_x,
            drv_y,
            p["driver_mount_pitch_X"],
            p["driver_mount_pitch_Y"],
            p["driver_mount_D"],
            z0,
            key,
        )


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

        xy = root.xYConstructionPlane
        base = create_base_plate(root, xy, p)
        top_plane = create_offset_plane(root, xy, p["plate_T"])
        cut_round_notches(root, top_plane, p)
        cut_bracket_mount_holes(root, top_plane, p)

        create_wheel_modules(root, xy, p)
        create_motor_brackets(root, xy, p)
        create_core_hardware(root, xy, p)

        for body in root.bRepBodies:
            if "base_plate" in body.name:
                assign_body_appearance(design, body, "Aluminum - Satin")
            elif "wheel" in body.name:
                assign_body_appearance(design, body, "Rubber - Black")
            elif "battery" in body.name:
                assign_body_appearance(design, body, "Plastic - Matte (Blue)")
            elif "driver" in body.name:
                assign_body_appearance(design, body, "Plastic - Matte (Green)")
            elif "fuse" in body.name:
                assign_body_appearance(design, body, "Plastic - Matte (Red)")

        ui.messageBox(
            "Note: the small cylinder between wheel and motor is the 20 mm coupler placeholder.\n\n"
            "Chassis layer 1 v0.1 concept model created.\n"
            "This is a spatial validation model, not a fabrication-ready drawing.\n\n"
            "Base plate: %.1f x %.1f x %.1f mm\n"
            "Wheel edge cutouts: 4 x %.1f x %.1f mm, R%.1f\n"
            "Wheel body: D%.1f x %.1f mm\n"
            "Battery tray envelope: %.1f x %.1f x %.1f mm\n"
            "Battery body envelope: %.1f x %.1f x %.1f mm\n"
            "Wheelbase / track: %.1f / %.1f mm\n"
            "Axle center below plate underside: %.1f mm\n"
            "Motor axial envelope: %.1f mm\n\n"
            "Motor top clearance below bracket chassis-mount inner face: %.1f mm\n"
            "Bracket motor-mount face is simplified as a flat %.1f mm plate.\n\n"
            "Please inspect wheel clearance, bracket holes, and first-layer hardware overlap in Fusion."
            % (
                p["plate_L"],
                p["plate_W"],
                p["plate_T"],
                p["cutout_L"],
                p["cutout_depth"],
                p["cutout_R"],
                p["wheel_D"],
                p["wheel_W"],
                p["battery_tray_X"],
                p["battery_tray_Y"],
                p["battery_tray_H"],
                p["battery_body_X"],
                p["battery_body_Y"],
                p["battery_body_H"],
                p["wheelbase"],
                p["track_width"],
                abs(axle_z(p)),
                p["motor_gearbox_L"] + p["motor_body_L"] + p["motor_encoder_L"],
                p["axis_to_plate_underside"] - p["motor_D"] / 2.0,
                p["bracket_motor_face_T"],
            )
        )

    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

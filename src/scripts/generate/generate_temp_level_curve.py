character_curve_names = [
    "Chara_1",
    "normal",
    "linear",
    "ease"
]

equipment_curve_names = [
    "acc3_hp",
    "acc3_atk",
    "acc3_def",

    "acc4_hp",
    "acc4_atk",
    "acc4_def",

    "acc5_hp",
    "acc5_atk",
    "acc5_def",

    "cos_rare3",
    "cos_rare4",
    "cos_rare5",

    "wp_rare3",
    "wp_rare4",
    "wp_rare5",

    "linear"
]

curve_template = {
    "CurveId": "CurveName",
    "Levels": []
}


def generate_level_curve():
    values = []

    for i in range(100):
        values.append(i / 100)

    return values


def generate_temp_curve_list(curve_name_list):
    curve_list = []

    temp_curve = generate_level_curve()
    temp_curve[0] = 100.0

    for curve_name in curve_name_list:
        new_curve = curve_template.copy()

        new_curve["CurveId"] = curve_name
        new_curve["Levels"] = temp_curve

        curve_list.append(new_curve)

    return curve_list


def generate_character_curve_list():
    return generate_temp_curve_list(character_curve_names)


def generate_equipment_curve_list():
    return generate_temp_curve_list(equipment_curve_names)
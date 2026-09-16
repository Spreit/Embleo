import json


def adapt_debug_sequence_list(sequence_list):
    adapted_sequence_list = []

    for setting in sequence_list:
        category = list(setting.keys())[0]

        new_seq = {}

        ID = setting[category][0]["id"]

        if "pl" in ID:
            new_seq["CharacterId"] = ID
        else:
            new_seq["EnemyId"] = ID

        new_seq["Category"] = category
        new_seq["Data"] = json.dumps(setting)  # Born to be a JSON, forced to be a string

        for individual_setting in setting[category]:
            pass
        
        adapted_sequence_list.append(new_seq)

    return adapted_sequence_list


def adapt_debug_sequences_master_data(input_file_path, output_folder):
    adapted_sequences = []

    debug_seqs: list

    with open(input_file_path, "r") as f:
        debug_seqs = json.load(f)

    # In original file the sequences are grouped by type
    attack_list = debug_seqs["attackList"]
    move_list = debug_seqs["moveList"]
    parameter_list = debug_seqs["updateParameterList"]
    # no_use = debug_seqs["noUse"]  # Well, we are using it, all right

    adapted_sequences.extend(adapt_debug_sequence_list(attack_list))
    adapted_sequences.extend(adapt_debug_sequence_list(move_list))
    adapted_sequences.extend(adapt_debug_sequence_list(parameter_list))

    character_sequences = []
    enemy_sequences = []

    for entry in adapted_sequences:
        if "CharacterId" in entry:
            character_sequences.append(entry)
        else:
            enemy_sequences.append(entry)

    # Sort by ID
    character_sequences = sorted(character_sequences, key=lambda x: x['CharacterId'])
    enemy_sequences = sorted(enemy_sequences, key=lambda x: x['EnemyId'])

    with open(output_folder + "CharacterSequenceMasterData.json", "w") as of:
        json.dump(character_sequences, of, indent=4)

    with open(output_folder + "EnemySequenceMasterData.json", "w") as of:
        json.dump(enemy_sequences, of, indent=4)


if __name__ == "__main__":
    adapt_debug_sequences_master_data("./SequenceMasterDataObject.json", "./")

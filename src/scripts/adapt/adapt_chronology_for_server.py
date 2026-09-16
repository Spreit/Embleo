import os
import json

# Splits extracted japanese chronology into per-character chronology json files
# (english chronology doesn't have episode order)

character_assosiation = {
    "pl017": "Edouard",
    "pl018": "Ana-Maria",
    "pl019": "Raoul",
    "pl020": "Lydie",
    "pl021": "Charles"
}

jp_char_name_to_id = {
    "＝エド": "pl017",
    "＝エドワール": "pl017",
    "＝アナマリア": "pl018",
    "＝ラウル": "pl019",
    "＝リディ": "pl020",
    "＝シャルル": "pl021",
}

#       Regular
# "m_Id": "c0982_pl001_001_desc"
# 	ChronologyId - c0982_pl001_001
# 	"Year": 0982,
# 	"Order": 1,

#       Episode
# "m_Value": "エピソード１"
# 	take char id form chronology id
# 	episode number from this

# Adventurers
# c0978_adv_001_desc

chronology_event_template = {
    "ChronologyId": "",
    "Year": 0,
    "Order": 0,
    "EpisodeId": "",
    "AdventureNo": 0
}

chronology_file_template = {
    "Chronologies": [{
        "Events": []
    }]
}


def generate_character_chronology_json(jp_chronology_json_path, output_folder):
    chr_entries = []

    with open(jp_chronology_json_path, "r", encoding="UTF-8") as f:
        chr_entries = json.load(f)["m_Entries"]

    chronology_parsed = {}
    # Parse data per character for easy handling:
    for entry in chr_entries:
        desc_id = entry["m_Id"]
        desc_value = entry["m_Value"]

        year, char_id, order, _ = desc_id.split("_")

        chronology_id = desc_id[:-5]

        if char_id not in chronology_parsed:
            chronology_parsed[char_id] = {}
            # print(char_id)

        chronology_parsed[char_id][chronology_id] = desc_value

    # print(len(chronology_parsed["adv"]))

    os.makedirs(output_folder, exist_ok=True)
    for char_id in chronology_parsed.keys():
        # print(char_id)

        chronology_file = {
            "Chronologies": [{
                "Events": []
            }]
        }

        for chronology_id, desc_value in chronology_parsed[char_id].items():
            event_entry = {}

            year, char_id, order = chronology_id.split("_")

            year_int = int(year[1:])
            order_int = int(order)

            event_entry["ChronologyId"] = chronology_id
            event_entry["Year"] = year_int
            event_entry["Order"] = order_int

            if ("pl" in char_id) and ("エピソード" in desc_value):
                ep_num = int(desc_value[-1])
                episode_id = char_id + "_" + "ep00" + str(ep_num)
                event_entry["EpisodeId"] = episode_id

            elif ("adv" in char_id) and ("冒険者の記録" in desc_value):
                # print(chronology_id)
                adv_ep_and_num, char_name_and_num = desc_value.split()

                char_name = char_name_and_num[:-2]
                char_ep_id = jp_char_name_to_id[char_name]

                ep_num_str = char_name_and_num[-2:]

                episode_id = char_ep_id + "_" + "ep0" + ep_num_str

                event_entry["EpisodeId"] = episode_id

                adv_ep_num = int(adv_ep_and_num[len("冒険者の記録"):])
                event_entry["AdventureNo"] = adv_ep_num

            chronology_file["Chronologies"][0]["Events"].append(event_entry)

            # Save chronology file
            with open(output_folder + char_id + ".json", "w") as output_file:
                json.dump(chronology_file, output_file, indent=4)


if __name__ == "__main__":
    generate_character_chronology_json("./Data list/Chronology JP.json")

def adapt_debug_scenario_party(debug_condition, scenario_id):
    condition_entry = debug_condition["ProgressEditParty"]

    adapted_entry = {
        "ProgressEditPartyId": scenario_id,
        "PartyPlayers": condition_entry["partyPlayers"],
    }

    return adapted_entry

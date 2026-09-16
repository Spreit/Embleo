import json


def SerVec3toVec3(SerializableVector3):
    vector_3 = [
        SerializableVector3["x"],
        SerializableVector3["y"],
        SerializableVector3["z"]
    ]

    return vector_3


def adapt_debug_enemy_master_data(DebugMasterData):
    AdaptedMasterData = []

    for entry in DebugMasterData["EnemyDatas"]:
        adapted_entry = {
            "EnemyId": entry["ID"],
            "Name": entry["Name"],
            "PrefabName": entry["PrefabName"],

            "EffectPath": "",  # Missing
            "SoundPath": "",  # Missing

            "DamageSe": entry["DamageSe"],
            "DownSe": entry["DownSe"],

            "HPGaugeDispDistance": entry["HPGaugeDispDistance"],
            "HPGaugeOffset": entry["HPGaugeOffset"],

            "CounterGaugeDispDistance": entry["CounterGaugeDispDistance"],
            "CounterGaugeOffset": SerVec3toVec3(entry["CounterGaugeOffset"]),
            "PushPriority": entry["PushPriority"],

            "ColliderSize": SerVec3toVec3(entry["ColliderSize"]),
            "ColliderCenter": SerVec3toVec3(entry["ColliderCenter"]),
            "HitColliderSize": SerVec3toVec3(entry["HitColliderSize"]),
            "HitColliderCenter": SerVec3toVec3(entry["HitColliderCenter"]),
            "DeadEffectSize": SerVec3toVec3(entry["DeadEffectSize"]),
            "DeadEffectOffset": SerVec3toVec3(entry["DeadEffectOffset"]),

            "ChaseWalkSpeed": entry["ChaseWalkSpeed"],
            "ReturnWalkSpeed": entry["ReturnWalkSpeed"],
            "SearchMoveAroundData": "",  # Missing
            "RecognitionApproachDistance": entry["RecognitionApproachDistance"],
            "AttackValidDistance": entry["AttackValidDistance"],
            "BlowAwayRate": entry["BlowAwayRate"],
            "EnemyWeight": entry["EnemyWeight"],
            "Scale": entry["Scale"],

            "IsBoss": bool(entry["IsBoss"]),
            "IsTargeting": bool(entry["IsTargeting"]),
            "IsBlowAway": bool(entry["IsBlowAway"]),
            "IsDamageMotion": bool(entry["IsDamageMotion"]),
            "IsCharacterController": bool(entry["IsCharacterController"]),
            "IsDownMotion": bool(entry["IsDownMotion"]),
            "IsHostReaction": bool(entry["IsHostReaction"]),

            "VisualCharacterId": entry["VisualCharacterId"],
            "StunSequenceStopTiming": entry["StunSequenceStopTiming"],
            "EnemyParam": json.dumps(entry["EnemyParam"]),
            "IsSpecialSkillReaction": bool(entry["IsSpecialSkillReaction"]),
            "RotateSpeed": entry["RotateSpeed"],
            "SearchPriority": entry["SearchPriority"]
        }

        AdaptedMasterData.append(adapted_entry)

    return AdaptedMasterData

if __name__ == "__main__":
    # save_json("./Adapted MasterData/EnemyMasterData.json", adapt_debug_enemy_master_data(debug_enemy_master_data_path))
    pass

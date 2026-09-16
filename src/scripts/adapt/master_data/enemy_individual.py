import json


def adapt_debug_enemy_individual_master_data(DebugMasterData):
    AdaptedMasterData = []

    for entry in DebugMasterData["Datas"]:
        adapted_entry = {
            "Index": entry["IndividualId"],
            "EnemyId": entry["MasterId"],
            "DefaultAI": entry["DefaultAI"],
            "MaxHP": entry["_maxHp"],
            "Attack": entry["_attack"],
            "Exp": entry["_exp"],

            "TransformConditions": entry["TransformConditions"],
            "TransformParam": entry["TransformParam"],
            "TransformId": entry["TransformId"],
            "TransformAI": entry["TransformAI"],

            "DropId": "",  # Probably should be somewhere else
            "AttackRightNum": entry["AttackRightNum"],
            "RecoilLimit": entry["_recoilLimit"],
            "RecoilSequence": entry["RecoilSequence"],
            "BarrierParam": json.dumps(entry["BarrierParam"]),

            "SummonEnemyIndividualIds": entry["_summonEnemyIndividualIds"],
            "EnemyIndividualParam": json.dumps(entry["EnemyIndividualParam"]),
            "SequenceCallName": entry["SequenceCallName"],
            "BadStatDurable": entry["_badStatusDurableLimits"],
            "BadStatDurableAdd": entry["_badStatusDurableOverLimitAddValues"],

            "ValidAttackType": entry["_validAttackType"],
            "DeadStaging": bool(entry["DeadStaging"]),
            "DeadRemoveOutOfView": bool(entry["DeadRemoveOutOfView"]),
            "AttackBreakParam": json.dumps(entry["AttackBreakParam"]),
            "AttrDamageRate": entry["_attributeDamageRates"],

            "ForcedPowerControl": False,  # No idea where to get this
            "RecoilDecreaseSpeed": entry["RecoilDecreaseSpeed"],
            "DownTime": entry["DownTime"],
            "ReviveNum": entry["_revivalNum"]
        }

        AdaptedMasterData.append(adapted_entry)

    return AdaptedMasterData


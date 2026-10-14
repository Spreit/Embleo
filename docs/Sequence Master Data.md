# Sequence Master Data

This reference describes `src/data/extract/masterdatadebug/SequenceMasterDataObject.json`: character/enemy combat sequences, not episode progression. Examples/counts are from the current local extraction and can change after setup. Enum meanings are not defined by this JSON.

## Root Fields

| Field | JSON type | Example |
| --- | --- | --- |
| `m_GameObject` | object | Unity metadata |
| `m_Enabled` | integer | `1` |
| `m_Script` | object | Unity metadata |
| `m_Name` | string | `SequenceMasterDataObject` |
| `attackList` | array of wrapper objects | 30 wrappers / 479 settings |
| `moveList` | array of wrapper objects | 29 wrappers / 387 settings |
| `updateParameterList` | array of wrapper objects | 20 wrappers / 876 settings |
| `noUse` | integer | `1`; meaning unknown |

Each wrapper has one category key (`AttackSetting`, `MoveSetting`, or `UpdateParameterSetting`) whose value is an array. Identify a record by `(collection, category, id, sequenceName)`; an owner/name pair can occur in more than one collection.

## Record Fields

The example column uses `ownerID / sequenceName`.

| Collection / category | Field | JSON type | Example |
| --- | --- | --- | --- |
| AttackSetting | `id` | string | `pl007` |
| AttackSetting | `sequenceName` | string | `Attack1` |
| AttackSetting | `baseInfo` | object | `pl007 / Attack1` |
| AttackSetting | `totalClipCount` | integer | `1` |
| AttackSetting | `clipCount` | array | `[]` |
| AttackSetting | `clipDatas` | array of objects | `pl007 / Attack1`, one clip |
| MoveSetting | `id` | string | `pl007` |
| MoveSetting | `sequenceName` | string | `Attack1` |
| MoveSetting | `totalMoveCount` | integer | `2` |
| MoveSetting | `moveCount` | array of integers | `[0, 1]` |
| MoveSetting | `direction` | array of vector objects | `[ {"x":0,"y":0,"z":1}, ... ]` |
| MoveSetting | `speed` | array of numbers | `[1.2, 1.5]` |
| UpdateParameterSetting | `id` | string | `pl001` |
| UpdateParameterSetting | `sequenceName` | string | `Charge1` |
| UpdateParameterSetting | `totalClipCount` | integer | `1` |
| UpdateParameterSetting | `clipCount` | array | `[]` |
| UpdateParameterSetting | `clipDatas` | array of objects | `pl001 / Charge1` |

## Attack `baseInfo`

Types and values below are from `pl007 / Attack1`.

| Field | JSON type | Example value |
| --- | --- | --- |
| `ChargeType` | integer | `0` |
| `IsInvincible` | integer | `0` |
| `IsSuperArmor` | integer | `0` |
| `IsArmor` | integer | `0` |
| `IsStrongAttack` | integer | `0` |
| `IsFloating` | integer | `0` |
| `IsForceDamageAction` | integer | `0` |
| `SearchDistance` | number | `15.0` |
| `ValidSearchLayerDistance` | number | `-1.0` |
| `OffsetFront` | number | `0.3` |
| `OffsetSide` | number | `0.5` |
| `OffsetRear` | number | `0.6` |
| `PriorityType` | integer | `0` |
| `PriorityFlag` | integer | `0` |
| `ServiceFlags` | integer | `0` |
| `NoSetTarget` | integer | `0` |
| `DamageCutRate` | number | `0.0` |
| `MultiTargetKey` | string | `""` |
| `IsForceMultiTarget` | integer | `0` |
| `KeepExistTarget` | integer | `0` |
| `BuffKey` | string | `""` |
| `ActionUniqueKey` | string | `""` |
| `IsWeakInvincible` | integer | `0` |

The `Is...` fields are integer values, not JSON booleans. `...Type`, `...Flag`, and similar integer fields may be enums/bit fields; the numeric meanings need external/runtime evidence.

## Attack `clipDatas`

Direct fields at `pl007 / Attack1 / clip 0`. Every one of the 594 clip records in this extraction has object values for all 18 `clip_` slots; slot presence alone does not identify an active action.

| Field | JSON type | Example owner / sequence |
| --- | --- | --- |
| `hitSetting` | object | `pl007 / Attack1` |
| `clip_AreaGuard` | object | `pl007 / Attack1` |
| `clip_Attack` | object | `pl007 / Attack1` |
| `clip_Charging` | object | `pl007 / Attack1` |
| `clip_DeathBall` | object | `pl007 / Attack1` |
| `clip_Grenade` | object | `pl007 / Attack1` |
| `clip_Gun` | object | `pl007 / Attack1` |
| `clip_HomingGun` | object | `pl007 / Attack1` |
| `clip_Laser` | object | `pl007 / Attack1` |
| `clip_LookGun` | object | `pl007 / Attack1` |
| `clip_MinionAttack` | object | `pl007 / Attack1` |
| `clip_MinionDecoyBomb` | object | `pl007 / Attack1` |
| `clip_MinionOrder` | object | `pl007 / Attack1` |
| `clip_Plunging` | object | `pl007 / Attack1` |
| `clip_PutShoot` | object | `pl007 / Attack1` |
| `clip_RegisterBuff` | object | `pl007 / Attack1` |
| `clip_SpecialSkillMagic` | object | `pl007 / Attack1` |
| `clip_Summon` | object | `pl007 / Attack1` |
| `clip_ThrowWeapon` | object | `pl007 / Attack1` |
| `enemy_Hit` | object | `pl007 / Attack1` |
| `enemy_ColliderHit` | object | `pl007 / Attack1` |
| `enemy_Throw` | object | `pl007 / Attack1` |
| `enemy_LinkThrow` | object | `pl007 / Attack1` |
| `enemy_AdditionalLinkThrow` | array | `[]` |
| `enemy_Intermittent` | object | `pl007 / Attack1` |
| `enemy_Laser` | object | `pl007 / Attack1` |
| `enemy_Grab` | object | `pl007 / Attack1` |
| `enemy_CatchAttack` | object | `pl007 / Attack1` |
| `general` | object | `pl007 / Attack1` |

Example populated slots for owner `pl007`, sequence `Attack1`, clip `0`: `clip_AreaGuard`, `clip_Attack`, `clip_Charging`, `clip_DeathBall`, `clip_Grenade`, `clip_Gun`, `clip_HomingGun`, `clip_Laser`, `clip_LookGun`, `clip_MinionDecoyBomb`, `clip_Plunging`, `clip_PutShoot`, `clip_Summon`, and `clip_ThrowWeapon`.

### `clip_Attack` example fields

Types and example values are from `pl007 / Attack1 / clip 0 / clip_Attack`.

| Field | JSON type | Example value |
| --- | --- | --- |
| `ClipIndex` | integer | `0` |
| `StrongAttack` | integer | `0` |
| `AttackDamageRate` | number | `0.7` |
| `ReactionType` | integer | `1` |
| `BlowAwayRate` | number | `1.0` |
| `StunTime` | number | `0.0` |
| `HitSE` | string | `se100069` |
| `HitEffect` | string | `""` |
| `AIPlayerIgnoreHitSE` | integer | `0` |
| `AttractDuration` | number | `0.0` |
| `DamageReceiverValidTime` | number | `0.0` |
| `MainAttribute` | integer | `0` |
| `OptionHitCount` | integer | `0` |
| `BadStatusList` | array | `[]` |
| `BuffKey` | string | `SequentialAttack` |
| `CriticalRate` | number | `-1.0` |
| `EventAttack` | integer | `0` |
| `StopDyingBoss` | integer | `0` |
| `HateOnly` | integer | `0` |
| `ForceReaction` | integer | `0` |
| `ForceCounterAttack` | integer | `0` |
| `IgnoreUnregisterKey` | string | `""` |
| `LimitPartsHitCount` | integer | `0` |
| `ForceReactionCancel` | integer | `0` |
| `AttackCenter` | object | `{x:-0.8,y:0,z:0.66}` |
| `AttackRadius` | number | `1.0` |
| `AttackSize` | number | `3.0` |
| `AttackDirection` | integer | `0` |
| `AttackListNoReflesh` | integer | `0` |
| `JudgementPartsName` | integer | `7` |
| `IsSurefire` | integer | `0` |
| `IsFindCapsuleCollider` | integer | `0` |

`hitSetting` contains `HitStopPower` (number), `HitStopTime` (number), `HitStopFlag` (integer), `AttackShakePower` (number), `AttackShakeTime` (number), and `IsForceAttackShake` (integer). Vectors contain numeric `x`, `y`, and `z` fields.

## UpdateParameter Clip Fields

Example owner: `pl001 / Charge1 / clip 0`.

| Field | JSON type | Child fields |
| --- | --- | --- |
| `attackBaseInfo` | object | same fields as Attack `baseInfo` |
| `clip_SpecialSkillMagic` | object | `ClipIndex` integer; `Buffs` array |
| `clip_EnemyReceiveDamage` | object | `DamageRate` number; `IsGuard` integer |

## Owner Coverage

Counts are settings in the current extraction. The 20 owners with UpdateParameter data are exactly `pl001` through `pl020` in this snapshot.

| Owner ID | Attack settings | Move settings | UpdateParameter settings |
| --- | ---: | ---: | ---: |
| `em0010_008` | 10 | 13 | 0 |
| `em0010_009` | 10 | 13 | 0 |
| `em0010_022` | 16 | 22 | 0 |
| `em0010_024` | 16 | 22 | 0 |
| `em0012_011` | 11 | 18 | 0 |
| `em0019_008` | 17 | 22 | 0 |
| `em0019_009` | 17 | 22 | 0 |
| `pl001` | 12 | 13 | 43 |
| `pl002` | 13 | 5 | 45 |
| `pl003` | 15 | 12 | 42 |
| `pl004` | 17 | 10 | 43 |
| `pl005` | 23 | 16 | 44 |
| `pl006` | 17 | 13 | 42 |
| `pl007` | 19 | 12 | 47 |
| `pl008` | 14 | 13 | 49 |
| `pl009` | 25 | 13 | 45 |
| `pl010` | 27 | 9 | 40 |
| `pl011` | 14 | 12 | 43 |
| `pl012` | 22 | 12 | 43 |
| `pl013` | 21 | 17 | 48 |
| `pl014` | 15 | 13 | 45 |
| `pl015` | 15 | 14 | 45 |
| `pl016` | 28 | 11 | 45 |
| `pl017` | 14 | 13 | 47 |
| `pl018` | 15 | 11 | 39 |
| `pl019` | 15 | 13 | 41 |
| `pl020` | 31 | 15 | 40 |
| `pl021` | 4 | 1 | 0 |
| `pl601` | 4 | 7 | 0 |
| `pl603` | 2 | 0 | 0 |

## Find Filled Clip Values

This prints concrete `clip_` slot values for every attack sequence of one owner. It preserves the sequence name and owner ID so records that reuse a name across collections are not confused.

```python
import json

data = json.load(open("src/data/extract/masterdatadebug/SequenceMasterDataObject.json", encoding="utf-8"))
owner_id = "pl007"

for wrapper in data["attackList"]:
    category, settings = next(iter(wrapper.items()))
    for setting in settings:
        if setting["id"] != owner_id:
            continue
        for clip_index, clip in enumerate(setting["clipDatas"]):
            for field, value in clip.items():
                if field.startswith("clip_"):
                    print(owner_id, setting["sequenceName"], clip_index, field, value)
```

## Observed Irregularities

| Check | Current observation | Example |
| --- | --- | --- |
| `clipCount` | Empty in all 479 Attack and 876 UpdateParameter settings; use `clipDatas` for actual clip records | `pl007 / Attack1` |
| `totalClipCount` vs. `len(clipDatas)` | Three Attack mismatches | `pl009 / Charge3` 7 vs. 6; `Charge5` 8 vs. 6; `Charge6` 9 vs. 6 |
| `totalMoveCount` vs. move-array length | Five mismatches; `moveCount`, `direction`, and `speed` lengths still agree | `em0010_008`, `_009`, `_022`, `_024` `Action044` 2 vs. 3; `em0012_011` `Action044` 1 vs. 2 |

These values are a snapshot, not validation rules. Do not truncate or synthesize data to make counts agree without runtime evidence.

## Adapter

`src/scripts/adapt/master_data/sequence.py` writes `CharacterSequenceMasterData.json` and `EnemySequenceMasterData.json`. It emits one row per owner/category wrapper with `CharacterId` or `EnemyId`, `Category`, and `Data` (the original wrapper encoded as a JSON string). IDs containing `pl` are classified as characters; other IDs as enemies. Generated files under `src/data/` are ignored; make durable transformations in tracked adapter/server code and validate the decoded `Data` string afterward.
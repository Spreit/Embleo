# Sequence Master Data Further Information

## Scope

`src/data/extract/masterdatadebug/SequenceMasterDataObject.json` is a Unity-serialized combat sequence database. It describes character and enemy attack clips, movement, and per-sequence parameter overrides. It does not describe episode progression or map gimmick state; those are separate data paths handled by the episode-data and scenario adapters.

This reference describes the extracted file and the adapter in `src/scripts/adapt/master_data/sequence.py`. Counts below describe the current local extraction and can change when game data is refreshed.

## File Shape

The root object contains Unity metadata (`m_GameObject`, `m_Enabled`, `m_Script`, `m_Name`) and four data members:

| Member | Current shape | Purpose |
| --- | --- | --- |
| `attackList` | 30 wrappers; 479 settings | Attack definitions, grouped under `AttackSetting` |
| `moveList` | 29 wrappers; 387 settings | Movement definitions, grouped under `MoveSetting` |
| `updateParameterList` | 20 wrappers; 876 settings | Per-sequence parameter overrides, grouped under `UpdateParameterSetting` |
| `noUse` | Integer (`1`) | Present in the source; runtime meaning unknown |

Each wrapper has one category key whose value is an array of settings. Use the full key `(collection, category, id, sequenceName)` to identify a record: the same owner and sequence name can occur in multiple collections because attack, movement, and update-parameter sequences are independent. In this extraction, IDs containing `pl` are treated as character IDs; other IDs are adapted as enemy IDs. This is the adapter's substring-based convention, not a universal type system.

## Setting Types

### Attack

An `AttackSetting` contains:

| Field | Meaning |
| --- | --- |
| `id` | Character or enemy sequence owner |
| `sequenceName` | Action/animation sequence key |
| `baseInfo` | Sequence-wide behavior and targeting modifiers |
| `totalClipCount` | Declared clip count |
| `clipCount` | Additional count array; empty in every attack/update setting in the current extraction |
| `clipDatas` | Per-clip data, including hit settings and action-specific payloads |

`baseInfo` fields in the current data:

| Field | Interpretation |
| --- | --- |
| `ChargeType` | Charge behavior/type enum; values are not defined here |
| `IsInvincible`, `IsSuperArmor`, `IsArmor`, `IsStrongAttack`, `IsFloating`, `IsForceDamageAction`, `NoSetTarget`, `IsForceMultiTarget`, `KeepExistTarget`, `IsWeakInvincible` | Boolean-like behavior switches stored as integers |
| `SearchDistance`, `ValidSearchLayerDistance` | Target-search distance controls |
| `OffsetFront`, `OffsetSide`, `OffsetRear` | Directional targeting offsets |
| `PriorityType`, `PriorityFlag`, `ServiceFlags` | Priority/service enum or flag values; definitions are not included |
| `DamageCutRate` | Damage-cut modifier; precise formula is not defined here |
| `MultiTargetKey`, `BuffKey`, `ActionUniqueKey` | Keys associated with multi-target behavior, buffs, or unique actions |

Each `clipDatas` item has a `hitSetting` object and typed payload slots. `hitSetting` contains `HitStopPower`, `HitStopTime`, `HitStopFlag`, `AttackShakePower`, `AttackShakeTime`, and `IsForceAttackShake` (hit pause and shake controls, inferred from the names).

The action payload slots include `clip_Attack`, `clip_Gun`, `clip_DeathBall`, `clip_Summon`, `clip_Laser`, `clip_ThrowWeapon`, `clip_HomingGun`, `clip_Charging`, `clip_Grenade`, `clip_PutShoot`, `clip_LookGun`, `clip_Plunging`, `clip_MinionOrder`, `clip_MinionAttack`, `clip_MinionDecoyBomb`, `clip_SpecialSkillMagic`, `clip_RegisterBuff`, and `clip_AreaGuard`. Enemy-oriented slots include `enemy_Hit`, `enemy_ColliderHit`, `enemy_Throw`, `enemy_LinkThrow`, `enemy_AdditionalLinkThrow`, `enemy_Intermittent`, `enemy_Laser`, `enemy_Grab`, and `enemy_CatchAttack`; `general` is also present. These are typed slots, not a promise that every slot is active for every clip.

Common payload fields include:

| Field/group | Interpretation |
| --- | --- |
| `ClipIndex` | Clip index within the sequence |
| `AttackDamageRate`, `DamageRate`, `AddDamageRate` | Damage modifiers for the containing attack/effect |
| `AttackCenter`, `AttackRadius`, `AttackSize`, `AttackDirection` | Hit-volume position, size, and direction controls |
| `ReactionType`, `BlowAwayRate`, `StunTime`, `StrongAttack`, `ForceReaction` | Hit reaction and knockback controls; enum values need external definitions |
| `HitSE`, `HitEffect`, `EffectPath`, `EffectName` | Sound/effect resource references |
| `MainAttribute`, `CriticalRate`, `BadStatusList`, `BuffKey` | Damage attribute and attached status/buff controls |
| `IsNoDamage`, `IsNoReactionDamage`, `IsIgnoreGuard`, `IsForceHit` | Boolean-like hit-resolution switches |
| `Delay`, `Interval`, `IterationNum`, `Duration`, `LifeTime` | Timing/repetition controls in applicable projectile or sustained-effect payloads |
| `Offset`, `Direction`, `Scale`, `Rotate` and vector-valued members | Spatial values; vectors are objects with `x`, `y`, and `z` components |

Payloads contain additional specialized fields. Projectile, laser, and throw slots include trajectory, homing, lifetime, collision, effect, and target-selection controls. Enemy hit slots include damage, hit reaction, guard, and hit-history controls. Interpret a field in the context of its containing payload; the same name in two payloads is not guaranteed to have identical behavior.

An observed `clip_Attack` payload also includes `AIPlayerIgnoreHitSE`, `AttractDuration`, `DamageReceiverValidTime`, `OptionHitCount`, `EventAttack`, `StopDyingBoss`, `HateOnly`, `ForceCounterAttack`, `IgnoreUnregisterKey`, `LimitPartsHitCount`, `ForceReactionCancel`, `AttackListNoReflesh`, `JudgementPartsName`, `IsSurefire`, and `IsFindCapsuleCollider`. Several are switches or enum-like values whose exact runtime semantics cannot be established from this dump alone. Preserve spelling such as `AttackListNoReflesh`; it is the serialized key.

### Movement

A `MoveSetting` contains `id`, `sequenceName`, `totalMoveCount`, `moveCount`, `direction`, and `speed`. `direction` is an array of `{x, y, z}` vectors; `speed` is an array of numeric values. `moveCount` holds per-step values. In the current extraction, all three arrays have equal lengths for all 387 settings and correspond by index. Units and value codebooks are not supplied.

### Update parameters

An `UpdateParameterSetting` contains `id`, `sequenceName`, `totalClipCount`, `clipCount`, and `clipDatas`. Its clip entries use:

| Field | Purpose |
| --- | --- |
| `attackBaseInfo` | Same base parameter set as `AttackSetting.baseInfo` |
| `clip_SpecialSkillMagic` | Special-skill clip index and buff list |
| `clip_EnemyReceiveDamage` | Incoming damage modifier and guard switch (`DamageRate`, `IsGuard`) |

These settings adjust combat behavior; they do not describe episode map gimmicks or chapter progression.

## Finding A Record

The raw file is large (about 82 MB in the current extraction), so avoid printing or searching the whole JSON as text. Load it as JSON and match both owner ID and sequence name. This read-only example prints the matching settings and their category:

```python
import json
from pathlib import Path

source = Path("src/data/extract/masterdatadebug/SequenceMasterDataObject.json")
data = json.loads(source.read_text(encoding="utf-8"))
owner_id = "pl009"
sequence_name = "Charge3"

for collection_name in ("attackList", "moveList", "updateParameterList"):
	for wrapper in data[collection_name]:
		category, settings = next(iter(wrapper.items()))
		for setting in settings:
			if setting.get("id") == owner_id and setting.get("sequenceName") == sequence_name:
				print(collection_name, category)
				print(json.dumps(setting, indent=2))
```

Change `owner_id` and `sequence_name` to the target values. If this prints no match, verify the owner spelling and search all three collections before concluding the sequence is absent.

## Reading Values Safely

- Integer fields named `Is...` are generally boolean-like, but preserve their original values unless the client enum is verified.
- Integer fields such as `...Type`, `...Flag`, `...Attribute`, and `...Direction` are enums or bit fields until proven otherwise. This JSON does not define their numeric codebooks.
- Floats are raw game parameters. Units, coordinate spaces, clamping, and multiplier-vs-absolute semantics are not documented here; use the containing field name and verified runtime behavior, not magnitude alone.
- `totalClipCount`/`totalMoveCount`, `clipCount`/`moveCount`, and the data arrays are separate source fields. Do not derive one from another without checking the sequence's runtime semantics.
- Empty/default payload slots are structural alternatives. Their presence does not imply that the slot participates in that attack.
- A `clipDatas` entry can contain every typed payload slot, including default-valued slots. Presence alone does not identify which slot the runtime uses; compare peer records and inspect the relevant consumer before changing one.

### Known source irregularities

These are observations from the current local extraction, not invariants for future game data:

- All 479 `attackList` settings and all 876 `updateParameterList` settings have an empty `clipCount` array. Use `clipDatas` to inspect the actual serialized clip entries; do not treat the empty array as proof that there are no clips.
- Three attack records have `totalClipCount` greater than the number of `clipDatas`: `pl009` / `Charge3` (7 vs. 6), `Charge5` (8 vs. 6), and `Charge6` (9 vs. 6). The reason is unknown; preserve this discrepancy unless runtime evidence explains it.
- Five movement records have a `totalMoveCount` that differs from the array length: enemy records `em0010_008`, `em0010_009`, `em0010_022`, and `em0010_024` (`Action044`, 2 vs. 3), and `em0012_011` (`Action044`, 1 vs. 2). Their `moveCount`, `direction`, and `speed` arrays still align with one another. Do not "fix" the declared count by truncating data without verifying the consumer.

Recompute these checks after refreshing assets. The upstream dump may change and may correct or add irregularities.

## Adapter Output

`adapt_debug_sequences_master_data` combines the top-level category lists and writes `CharacterSequenceMasterData.json` and `EnemySequenceMasterData.json`. It creates one adapted row per wrapper (normally one owner/category), not one row per `sequenceName`. Each row contains `CharacterId` or `EnemyId`, `Category`, and `Data`. `Data` is a JSON-encoded string containing the original category wrapper and its settings, rather than a normalized nested object. The adapter splits character from enemy records using the `id` substring check and sorts each output by owner ID.

The current extraction produces 65 character rows and 14 enemy rows (79 wrappers total). These are useful smoke-check counts for this asset version only; they are not stable API contracts.

The adapter makes several assumptions that matter when changing its code:

- Every wrapper has at least one category key, and the selected category contains at least one setting. It indexes the first key and the first setting without validation.
- The first setting's `id` determines the owner for the entire wrapper. All settings inside that wrapper are therefore assumed to belong to the same owner.
- An `id` containing the substring `pl` is classified as a character; every other ID is classified as an enemy. This is a naming heuristic, not a lookup against character/enemy master data.
- `Data` preserves the complete wrapper (including all settings), so changing its serialization shape changes the API's nested JSON string even though the outer adapted row is unchanged.
- The adapter builds output paths by string concatenation. A direct call must pass an `output_folder` ending in a path separator; the normal master-data adapter supplies one.

## Data Flow

The runtime path is:

1. `setup_server.py` extracts the Unity asset into `src/data/extract/masterdatadebug/SequenceMasterDataObject.json`.
2. `adapt_debug_master_data` calls `adapt_debug_sequences_master_data`.
3. The adapter writes `src/data/masterdata/CharacterSequenceMasterData.json` and `src/data/masterdata/EnemySequenceMasterData.json`.
4. `server.py` loads those files into `MasterGroup.characterSequences` and `MasterGroup.enemySequences`.
5. The episode API returns `MasterGroup` to the existing game client.

All three data paths are under ignored `src/data/`. They are generated local data, not durable source changes. Editing the extracted JSON or adapted JSON can be useful for a local experiment, but the edit will not be part of a commit and can be overwritten by setup. For a persistent fix, change the adapter or another tracked server-side transformation, and test its output against the local extraction.

## Change And Verify Workflow

1. **Identify the layer.** Decide whether the problem is in the extracted value, the adapter's transformation, the adapted output, or the response assembled by `server.py`. A correct raw value with a wrong adapted row points to the adapter; correct adapted files with a wrong response point downstream.
2. **Find the exact record.** Search by both owner `id` and `sequenceName`, then confirm the category (`AttackSetting`, `MoveSetting`, or `UpdateParameterSetting`). A wrapper can contain many settings; do not edit the first matching owner record without checking the name.
3. **Find the active nested payload.** Compare the full `clipDatas` entry with nearby clips and the same action on related owners. Preserve the original types, key casing, list structure, and clip ordering. Do not globally replace a repeated field name across payload families.
4. **Make the durable change.** Do not commit edits under `src/data/`. Put a reproducible transformation in tracked server/adaptation code. If a local raw-data edit is only a probe, record the intended value in the test or code before discarding the generated data.
5. **Regenerate the adapted files.** From `src/`, use the project environment to run the sequence adapter against the local extraction, writing to `./data/masterdata/`:

   ```python
   from scripts.adapt.master_data.sequence import adapt_debug_sequences_master_data

   adapt_debug_sequences_master_data(
	   "./data/extract/masterdatadebug/SequenceMasterDataObject.json",
	   "./data/masterdata/",
   )
   ```

   The output path ends in a separator because the adapter concatenates filenames onto it.
6. **Validate the output.** Parse both output files as JSON; check the expected owner and category; parse each row's `Data` string with `json.loads`; confirm the target `sequenceName` and nested values survived unchanged or changed as intended. Do not assert snapshot record counts as a permanent contract.
7. **Validate the serving layer.** Confirm `MasterGroup.characterSequences` or `MasterGroup.enemySequences` contains the row in the API response. If the response is correct but behavior is not, investigate the existing client-consumed schema/semantics or other server data; do not assume changing another similarly named field will help.

For a focused adapter test, call `adapt_debug_sequences_master_data` with a temporary output directory ending in a separator, then inspect the two generated files. Avoid rerunning the full asset download/extraction pipeline for an adapter-only change.
# Episode Gimmicks and Scenario Progression

## Scope

Episode map gimmicks and scenario-driven changes are assembled through separate data paths. This distinction matters for gates, doors, switches, traps, and other objects that can have both an initial map state and later scripted transitions.

The server exposes both paths in `EpisodeDetail`:

| Response field | Primary source | Role |
| --- | --- | --- |
| `LayoutGroup.Gimmicks` | Per-episode `EpisodeGimmickMasterDataObject.json`, plus applicable stage-option gimmicks | Places map objects and supplies their initial state, type, resource, scenario range, and type-specific parameters |
| `ScenarioGroup.Gimmicks` | Adapted episode scenario progress records | Applies object operations at specific scenario progress points |

These are not duplicate representations. A scenario operation can change or reset an object's layout state later in the episode.

## Data Path

1. Setup extracts Unity assets under `src/data/extract/`.
2. The episode-data adapter converts episode gimmick records to the server's layout representation. It maps the source ID, resource/master ID, action type, starting status, scenario range, and type-specific parameters.
3. The scenario adapter preserves gimmick operations from scenario progress records. The server groups those records while assembling `EpisodeDetail`.
4. `server.py` returns both groups with the episode response.

Built-in map gimmicks are resolved through the extracted `EpisodeMasterDataObject.json` location IDs and `StageLocationMasterDataObject.json` area records. A stage-option definition matching the area's `_id` takes precedence. If none exists, the adapter uses the final component of the area's `_resourcePath` to find the reused prefab's definition. The emitted `StageMapID` uses that resource name, rather than the location's area alias. For example, Ana-Maria Episode 2's `PLA01E_Area04` loads the `PLA01_Area04` prefab, whose root map object has the base name: its built-in gates receive `StageMapID: PLA01_Area04`. In contrast, `PLA01E_Area01` loads its own named map prefab, which explicitly references the same option-gimmick prefab as the daytime map, so its `StageMapID` remains `PLA01E_Area01`. Matching only area aliases can omit definitions; emitting aliases for reused prefabs can also mismatch their map-object names. The prefab names and option-prefab references are verified asset facts. An explicitly empty variant definition is preserved; duplicate map/gimmick pairs are emitted once.

The extracted and adapted files under `src/data/` are generated and ignored. For a persistent behavior change, update tracked adapter/server code rather than committing an edit to generated JSON.

## State Model

Layout gimmicks commonly contain an `EpisodeGimmickId`, an `ActionType`, and a `Status` array whose entries associate a state with a `ScenarioNo` range. Type-specific fields (for example, gate auto-close behavior) come from the gimmick's add-parameter data.

Scenario gimmick groups contain a `ProgressGimmickId` and a list of operations. Each operation commonly contains:

| Field | Use in the payload |
| --- | --- |
| `GimmickId` | Identifies the object being operated on |
| `StartType` | Source operation parameter; numeric meaning is not documented in this repository |
| `Status` | Requested state for this operation; do not assume it is an initial layout state |
| `Flag` | Additional source operation parameter; numeric meaning is not documented in this repository |

An object can occur in several progress groups, including a reset followed by an open/close transition. Keep progress IDs and operation ordering intact. Do not globally replace every operation for a matching `GimmickId` with its final state; that can erase intended transitions.

The numeric meanings of `Status`, `StartType`, and `Flag` are not defined by the extracted scenario JSON or adapter. Verify them against the game data/runtime before assigning semantics. Treat examples and observed values as data, not as an enum specification.

## Battle Skipping

`SKIP_BATTLES` is a server-side filter, not a general "mark all battle requirements complete" operation. In the current server implementation it omits `Kills` and `EnemyParams` from `ScenarioGroup`, and filters progress types 3 and 14 from the episode `Scenarios` list. Other progress groups and gimmick operations are assembled separately.

`skip_scenario` is a global progress-type filter applied only to `EpisodeDetail.Scenarios`, currently empty. ProgressType 5 represents gimmick scenarios; adding 5 removes every episode's type-5 entries. It does not remove `ScenarioGroup.Gimmicks`. A future episode-specific workaround should use an episode-scoped filter.

Consequences for debugging:

- An empty `ScenarioGroup.Kills` confirms the kill operations were omitted from that response; it does not set later gimmick operations to their completed state.
- A type-5 `skip_scenario` entry suppresses the corresponding scenario metadata entries across all episodes; it is not a per-gate override.
- `EnemyDetail` can still contain master records for enemies in the episode. Its length alone does not prove that an encounter is currently spawned or active.
- A later gate or switch operation may still carry a condition or flag even when the kill event is omitted. Any bypass should be explicit, scoped to the relevant episode and operation, and guarded by the server setting that requires it.
- Preserve the operation's `Status`, `StartType`, progress ID, and other gates' data unless runtime evidence says they must change. Do not modify the client/APK to compensate for a server payload issue.

## Debugging Workflow

1. Confirm which server revision is running before interpreting gameplay results.
2. Read the current resume point from `EpisodeDetailUser.startScenarioNo` in the episode-start response. See [Checkpoint and Save System](checkpoint%20and%20save%20system.md) for how this emulator handles checkpoints.
3. Inspect the same response's `LayoutGroup`, `ScenarioGroup`, and `Scenarios`. Distinguish initial layout state from scenario-time operations and check whether the expected progress point is before or after the saved start point.
4. Check whether the relevant kill/other progress event is included or filtered. Do not infer this from `EnemyDetail` alone.
5. Make the narrowest server-side transformation, then assert the assembled `EpisodeDetail` locally. Verify the live API payload after deployment before asking for an APK retest.

Scenario data is returned as part of a MessagePack API response. When inspecting it directly, decode the response and examine the named fields rather than relying on UI color or text alone; the latter can be useful symptoms but do not identify which payload field controls the behavior.

# Episode Gimmicks and Scenario Progression

## Episode Response

`src/server.py` assembles `EpisodeDetail` from layout data, adapted scenario
records, and event-drop data. Episode responses use MessagePack encoding.

| Response field | Source | Contents |
| --- | --- | --- |
| `LayoutGroup.Gimmicks` | Per-episode `EpisodeGimmickMasterDataObject.json` and applicable stage-option definitions | Object IDs, resources, initial states, scenario ranges, and type-specific parameters |
| `LayoutGroup.Breakables` | Per-episode `EpisodeBreakableMasterDataObject.json` | Breakable IDs and resource IDs |
| `LayoutGroup.Items` | The same breakable source records | Item entries describing breakable resources, scenario ranges, and stack/parallel counts |
| `Scenarios` | `src/data/masterdata/scenario/<episode_id>.json` | Progress metadata linking scenario numbers and progress types to progress IDs |
| `ScenarioGroup` | The same adapted scenario records | Progress details grouped by type, including gimmick operations and breakable conditions |
| `EventDrops` | Per-episode `EpisodeEventDropMasterDataObject.json` | Event-drop IDs and script paths |

Layout records describe objects and their initial state. Scenario records describe
progress conditions and operations associated with scenario progress points.
An object can have an initial layout state and several subsequent operations.

## Data Sources and Assembly

Setup extracts Unity assets under `src/data/extract/`. The episode layout adapter
in `src/scripts/adapt/adapt_debug_episode_data.py` reads per-episode files under
`src/data/extract/masterdatadebug/episode/<episode_id>/` and converts them into
`LayoutGroup` entries.

`src/scripts/adapt/adapt_debug_scenario.py` produces the adapted scenario records
under `src/data/masterdata/scenario/`. The server's
`fill_scenario_list_from_adapted_scenario` builds `Scenarios`, while
`fill_scenario_group_from_adapted_scenario` groups each record's `Progress`
payload by its `ProgressType`. These functions retain source record ordering
within the emitted lists, subject to the filters described below.

`fill_episode_detail_by_episode_id` combines the layout, scenario metadata,
scenario groups, and event drops. Extracted and adapted data files under
`src/data/` are generated and ignored by Git; their transformations are defined
in the tracked adapter and server code.

## Gimmick Layouts

`src/scripts/adapt/episode_data/gimmicks.py` maps each supported gimmick record
into the following common fields:

| Layout field | Source |
| --- | --- |
| `EpisodeGimmickId` | `_id` |
| `ResourceId` | `_masterID` |
| `ActionType` | `_typeID` |
| `Status` | One entry containing `_startStatus` and the source scenario range |
| `Scale` | `_modelScale`, converted to an `[x, y, z]` array |
| `ScenarioNo` | `[_startScenarioNo, _endScenarioNo]` |

Type-specific fields come from `_addParamJson`. For example, gate types 8 and 10
emit `Gate.AutoClose` from `_autoClose`; type 3 emits
`DirectionMove.WarpPointId` from `_warpPointID`. Unsupported action types and
type 2 are omitted by the adapter.

Built-in stage-option gimmicks are resolved through the episode's location IDs
in `EpisodeMasterDataObject.json` and the area records in
`StageLocationMasterDataObject.json`. Area records with `_situation == 0` supply
the map IDs and resource paths.

A stage-option definition matching the area's `_id` takes precedence, including
an explicitly empty definition. Otherwise, the adapter uses the final component
of the area's `_resourcePath` to find the reused prefab's definition. Emitted
`StageMapID` values use that resource name. Area aliases and prefab resource
names can differ. Duplicate area/gimmick ID pairs are emitted once.

For example, `PLA01E_Area04` loads the `PLA01_Area04` prefab, whose root map
object uses the base name, so its built-in gimmicks receive
`StageMapID: PLA01_Area04`. In contrast, `PLA01E_Area01` loads its own named map
prefab, which references the daytime map's option-gimmick prefab; its emitted
`StageMapID` remains `PLA01E_Area01`. Sharing option-gimmick definitions does
not necessarily mean sharing the root map-object name.

## Scenario Gimmick Operations

Progress type 5 maps to `ScenarioGroup.Gimmicks`.
`src/scripts/adapt/scenario/gimmick.py` emits a `ProgressGimmickId` and a
`Gimmicks` list containing the source `GimmickOperations` records without
transforming their fields.

| Operation field | Representation |
| --- | --- |
| `GimmickId` | ID of the referenced object |
| `StartType` | Source operation parameter |
| `Status` | State value carried by this operation |
| `Flag` | Additional source operation parameter |

The numeric meanings of `Status`, `StartType`, and `Flag` are not defined by
these adapters. A scenario operation's `Status` is separate from the initial
`Status` in the object's layout. The same object ID can occur in several
progress groups with different operation parameters.
For example, an object can have a reset operation followed by an open/close
transition. These are separate progress records rather than one final state
for the object.

## Breakable Layouts and Conditions

The client separates network definitions in `Game.Net` from the runtime data
model in `App.Data`. Extracted debug master data represents the latter; its
fields do not map directly to fields of the same-named network type.

`Game.Net.EpisodeBreakable` contains only `EpisodeBreakableId` and `ResourceId`.
`src/scripts/adapt/episode_data/breakables.py` maps `_id` and `_masterID` to these
fields in `LayoutGroup.Breakables`.

The same adapter also emits `Game.Net.EpisodeItem` records in `LayoutGroup.Items`:

| Item field | Source or value |
| --- | --- |
| `EpisodeItemId` | `_id` |
| `ItemDropMethod` | `2`, the value of `Game.Net.ItemDropMethod.Breakable` |
| `DropResourceId` | `_masterID` |
| `ObjectCount` | `_stackNum` |
| `ParallelNum` | `_parallelNum` |
| `EpisodeEvent` | `null` |
| `ScenarioNo` | `[_startScenarioNo, _endScenarioNo]` |

Source IDs, ordering, ranges, and counts are preserved, including zero counts.
The client builds item layouts from these item records. Its
`App.MasterDataManager.StoreEpisodeBreakableMasterData` matches item entries
with `ItemDropMethod.Breakable` to their layout IDs and passes them to
`App.Data.EpisodeBreakableInfo.Setup`. That method reads the resource from
`DropResourceId`, the stack count from `ObjectCount`, and the parallel count
from `ParallelNum`. It clamps each count to at least one. A layout without a
matching breakable item or static-item entry is omitted from the client's
breakable master data.

Progress type 17 maps to `ScenarioGroup.BreakableActions`.
`src/scripts/adapt/scenario/breakable_action.py` emits the progress `Id` and an
`Objects` list. Each object contains `Id` from the source `ObjectId` and `Count`
from the source condition count. Layout counts and condition counts are
separate fields; the adapter does not derive one from the other.

### Drop Data

`Game.Net.EpisodeDetailUser.Drops` contains `EpisodeDropUser` records with
`Target`, `TargetId`, and `Items`. `EpisodeDropTarget.Breakable` has value `2`.
Each `EpisodeDropItemUser` contains `DropId`, `Type`, `ItemId`, and `Count`.
`EpisodeDropItemType` values are `Unknown = 0`, `Gold = 1`, `Item = 2`,
`Equipment = 3`, and `Recipe = 4`.

The client passes a drop record with a matching `TargetId` into
`EpisodeBreakableInfo.Setup`, which converts its items into runtime drop data.
That setup path accepts a missing drop record; drops are separate from the
item entry used to construct the breakable.

The source breakable records contain `_dropLotteryID` and `_drops`, but the
server's breakable adapter does not resolve lotteries or populate user drop
records. The episode start and continue response templates contain empty
`drops` lists. `EpisodeDetail.EventDrops` is a separate list of script references:
its adapter maps `ID` to `Id` and `_targetRequirements` to `ScriptPath`.

## Scenario Filters

The following settings in `src/server.py` control which scenario records are
included in the response:

| Setting | `Scenarios` effect | `ScenarioGroup` effect |
| --- | --- | --- |
| `DISABLE_SCENARIOS` | Leaves the metadata list empty when enabled | Groups are still assembled |
| `skip_scenario` | Omits the listed progress types across episodes; the list is empty in the source | No effect |
| `SKIP_BATTLES` | Omits types 3 and 14 | Omits `Kills` and `EnemyParams` |
| `SKIP_VIDEOS` | Omits type 6 | Omits `Demos` |
| `SKIP_ROUTE_FORK_MERGE` | Omits types 11 and 12 | Omits `RouteForks` and `RouteMerges` |

Both scenario assembly functions omit progress types greater than 100.
Checkpoint progress records included in `ScenarioGroup.CheckPoints` have
`RequestSave` set to `True` by the server.

These filters omit records; they do not change gimmick layout states or rewrite
remaining gimmick operations. For example, adding type 5 to `skip_scenario`
omits its metadata from `Scenarios` while leaving `ScenarioGroup.Gimmicks`
intact. `EnemyDetail` is assembled separately from episode enemy master records
and does not represent the currently spawned encounter list.
Omitting a kill event does not mark its requirements complete or resolve
conditions and flags carried by later gate or switch operations.

## Episode Resume Point

The episode-start response carries the resume scenario number in
`EpisodeDetailUser.startScenarioNo`. The server fills this value from its saved
checkpoint when an entry exists for the episode. Checkpoint persistence is
described in [Checkpoint and Save System](checkpoint%20and%20save%20system.md).

# Enemy parents and generators

This investigation covers Bastien episode 1 (`pl011_ep001`) and the current episode adapter. It identifies a concrete parent-formation defect and the client-side spawning paths. It does **not** establish a complete explanation for every reported generator failure; no gameplay fix was implemented or tested.

## Who spawns the children?

The client does. The server must publish complete episode enemy definitions and their supporting master data. Child spawning does not require an additional HTTP request for each child or a server timer that inserts enemies into the scene.

The native client has `EnemyManager.CreateEnemyChild`, `CreateEnemyChildInternal`, `CreateEnemySummon`, and `CreateEnemyForSummon`. `EpisodeEnemyMasterData.Setup` calls `EpisodeEnemyInfo.CreateExternalEnemyInfoList`, which creates derived enemy definitions for parent children and generator targets. `CreateExternalEnemyInfo` resolves an enemy **individual** through `EnemyIndividualInfo.GetInfo`, then resolves its base enemy through `EnemyInfo.GetEnemyInfo`.

Consequently, do not replace the references in `EnemyIds` or `_summonEnemyData.EnemyId` with an arbitrary placed enemy's `_id`. Despite the network field name `SummonRule.EpisodeEnemyId`, the inspected external-definition path uses the supplied value as an enemy individual ID. A target need not have its own placed entry in the episode file.

## Role numbers are already correct

| Extracted `_enemyType` | Network `RoleType` | Meaning |
| --- | --- | --- |
| 0 | 1 | Normal |
| 1 | 2 | Parent |
| 2 | 3 | Generator |

`src/scripts/adapt/episode_data/enemies.py` already adds one. Sending the extracted numbers directly would introduce the network `Unknown` role and shift the other roles.

The installed `pl011_ep001` extraction contains 277 normal, 132 parent, and 69 generator rows. These counts describe this installed extraction, not every version of the episode.

## Parent formations: a confirmed adapter defect

The extracted child definition contains a **lookup key**, for example `FormationId = "3_1"`. Its formation is defined in:

`src/data/extract/masterdatadebug/PlatoonMasterDataObject.json`

That file contains `Datas` rows with `_id`, `Formation`, and `FormationPadding`. The current adapter instead sends the lookup key directly as `Child.Formation` and omits `Child.FormationPadding`.

Those fields have different meanings. In the network-data path, `EpisodeEnemyInfo.Setup` copies `Child.Formation` into the runtime formation contents. `ChildEnemyData.GetFormationData` splits those contents into rows, splits each row on commas, and attempts to parse each occupied cell as an integer. A string such as `"3_1"` is not a formation grid and produces no valid numbered cells.

The debug/master-data path additionally supports `FormationId`: `CreateExternalEnemyInfoList` looks up `PlatoonInfo` and fills the contents and padding. The network `EpisodeEnemyChild` contract has **no FormationId field**, so publishing an ID as its `Formation` cannot substitute for that lookup.

To publish a working parent definition:

1. Resolve `_childEnemyData.FormationId` against the platoon master's `_id`.
2. Send the resolved row's complete `Formation` text in `Child.Formation`, preserving commas and row breaks.
3. Send its `FormationPadding` as the network vector representation.
4. Preserve the ordered `EnemyIds` array in `Child.Ids`.
5. Include the referenced enemy individual and base enemy masters, and ensure the parent itself is placed and admitted by its appearance/scenario rules.

The parser uses `0` as the parent anchor and subtracts one from a numbered cell to obtain `EnemyIdIndex`: `1` refers to `Child.Ids[0]`, `2` to `Child.Ids[1]`, and so on. Empty or whitespace cells are ignored. Do not reorder `Child.Ids` independently of the grid.

For example, the installed platoon `3_1` has two `1` cells and a `0` anchor, with padding `(1, 1)`. With one child individual in `Child.Ids`, those two cells select that same individual at two formation positions. The lookup key's first number is not a reliable child-count instruction.

## Generators: data requirements and remaining uncertainty

The adapter already publishes the extracted summon fields: target, initial count, minimum count, total count, offsets, ranges, named appearance point, death linkage, rotation, and additional-wave position parameters.

`EnemyManager.CreateEnemySummon` checks `SummonEnemyData.IsValid`, reads `InitialAppearNum`, and calls `CreateEnemyForSummon(enemy, initialCount, false)`. The generator branch of `CreateExternalEnemyInfoList` creates a derived definition from the summon target individual. This is separate from the parent's formation grid; resolving platoon data alone is not a demonstrated fix for generator failures.

In this installed episode, generators reference `em0023_001_02` and `em0011_001_03`. Both exist in `EnemyIndividualMasterData.json`. Neither is a matching episode `_id`; that is not, by itself, an error.

There is an additional server completeness gap: `fill_enemy_detail_by_episode_id` in `src/server.py` includes placed individual IDs and parent child IDs, but does not collect summon targets. `em0011_001_03` is absent from that collected set for this episode. This merits correction and an asset/preload check, but the current server also publishes the global individual masters. The omission therefore does not prove that it explains every generator failure, especially barracks targeting the already included `em0023_001_02`.

Do not normalize zero summon limits without confirming their semantics. Some tower generators intentionally have `InitialAppearNum = 3`, `MinLimitNum = 0`, `TotalNum = 0`, `AppearPointName = "childpoint"`, and `DieWithChild = true`. Treating every zero total as “spawn nothing” would conflict with their nonzero initial count.

## Verification before implementing a fix

- Inspect the actual episode-start response, not only the extracted JSON: parent grids and padding must be resolved, roles correct, and summon fields retained.
- Check the individual-to-base-enemy master links and required model/AI assets for every target, including targets used only by generators.
- Test a parent with a known grid: child count, ordering, spacing, and positions relative to the parent anchor.
- Test an ordinary barracks generator separately from a tower with a named `childpoint`: initial wave, replacements after kills, limits, and death linkage.
- Verify the parent/generator's appearance rule, placement, scenario interval, and any stage rule that suppresses summoned groups. Avoid adding permanent standalone enemy placements merely to mask a broken spawning path.
- Repeat at a fresh episode start and at a resumed checkpoint; spawning and restore behavior are separate checks.

## Evidence locations

Source: `src/scripts/adapt/episode_data/enemies.py`; `src/server.py`, `fill_enemy_detail_by_episode_id` and global enemy master publication.

Local extracted data: `EpisodeEnemyMasterDataObject.json` for `pl011_ep001`, `PlatoonMasterDataObject.json`, and adapted `EnemyIndividualMasterData.json`. Game-derived assets were inspected locally and are not included in this document.

Native ARM64 reference points (build-specific RVAs):

| Method | RVA | Evidence |
| --- | --- | --- |
| `EpisodeEnemyInfo.Setup(EpisodeLayout, EpisodeEnemy, EpisodeDropUser)` | `0x3617340` | Copies network child contents, padding, and summon rule into runtime data |
| `ChildEnemyData.GetFormationData` | `0x3611790` | Parses comma-separated numeric cells; zero anchor and one-based child indexes |
| `EpisodeEnemyInfo.CreateExternalEnemyInfoList` | `0x3617960` | Separate parent/platoon and generator branches |
| `EpisodeEnemyInfo.CreateExternalEnemyInfo` | `0x3617B84` | Resolves individual and base enemy masters |
| `EpisodeEnemyMasterData.Setup` | `0x3617FD0` | Calls external-definition creation |
| `EnemyManager.CreateEnemyChild` | `0x17D7E04` | Client child-creation entry point |
| `EnemyManager.CreateEnemySummon` | `0x17D7F78` | Starts the initial summon count through `CreateEnemyForSummon` |
| `EnemyManager.CreateEnemyForSummon` | `0x17D5C54` | Client summon creation path |

The C# dumps supply type contracts and method addresses; the parsing, lookup, and initial-summon observations above were checked against native instructions. Actual in-game child spawning after a correction remains unverified.

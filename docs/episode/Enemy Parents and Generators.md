# Enemy parents and generators

This investigation covers Bastien episode 1 (`pl011_ep001`) and the current episode adapter. It identifies the parent-formation defect and the client-side spawning paths. The adapter now resolves parent grids and padding, publishes explicit external child/summon definitions for release clients, and includes generator-only targets in episode enemy detail. These changes are checked against installed Bastien data; other generators and resume behavior require separate gameplay checks.

## Who spawns the children?

The client does. The server must publish complete episode enemy definitions and their supporting master data. Child spawning does not require an additional HTTP request for each child or a server timer that inserts enemies into the scene.

The native client has `EnemyManager.CreateEnemyChild`, `CreateEnemyChildInternal`, `CreateEnemySummon`, and `CreateEnemyForSummon`. `EpisodeEnemyMasterData.Setup` calls `EpisodeEnemyInfo.CreateExternalEnemyInfoList` only when `EzDebugInfo.m_LocalBoot` is true. That debug-local builder creates derived enemy definitions for parent children and generator targets. Release clients obtaining network episode data require those external definitions in the response; publishing only the placed parent or generator is insufficient. `CreateExternalEnemyInfo` resolves an enemy **individual** through `EnemyIndividualInfo.GetInfo`, then resolves its base enemy through `EnemyInfo.GetEnemyInfo`.

Consequently, do not replace the references in `EnemyIds` or `_summonEnemyData.EnemyId` with an arbitrary placed enemy's `_id`. Despite the network field name `SummonRule.EpisodeEnemyId`, the inspected external-definition path uses the supplied value as an enemy individual ID. A target need not have its own placed entry in the episode file.

## External definitions required by release clients

The child/summon references remain enemy individual IDs. A separate network enemy definition must exist for each distinct nonempty target of each parent or generator. The native lookup key is exactly:

`Ext.<parent EpisodeEnemyId>.<enemy individual ID>`

For example, the first barracks uses `Ext.EM_CP01_001-Barracks01.em0023_001_02`. The external row has `EnemyId = em0023_001_02`, network normal role `1`, appearance type `External = 2`, and appearance count `1`. It inherits the parent's group and scenario interval; its child and summon definitions are null. The adapter emits these records after placed definitions, deduplicates repeated target IDs within each parent, and rejects collisions with existing episode IDs.

These are lookup definitions, not permanent standalone placements. Parent formation cells and the generator's count/position rules still control when and where children appear. The runtime constructs the same `Ext.` key and finds its corresponding construction data before creating a child. This is why a valid `SummonRule` and globally published individual master can still produce no soldiers when the external row is missing.

The generator creation coroutine awaits parent-child creation before calling `CreateEnemySummon`. `SummonEnemyData.IsValid` requires a nonempty target; `CreateEnemyForSummon` additionally requires local or host authority. Single-player spawning should use the local authority path. These client gates must be inspected if spawning remains absent after complete external definitions are published.

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

That file contains `Datas` rows with `_id`, `Formation`, and `FormationPadding`. The former adapter sent the lookup key directly as `Child.Formation` and used hardcoded `Child.FormationPadding`. The corrected adapter resolves the platoon from the installed master data before publishing both fields. A missing referenced formation raises a descriptive error instead of silently publishing an unusable lookup key.

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

`EnemyManager.CreateEnemySummon` checks `SummonEnemyData.IsValid`, reads `InitialAppearNum`, and calls `CreateEnemyForSummon(enemy, initialCount, false)`. The generator branch of `CreateExternalEnemyInfoList` creates a derived definition from the summon target individual. This is separate from the parent's formation grid; resolving platoon data alone does not supply the missing external summon definition. The release adapter now publishes that definition explicitly.

In this installed episode, generators reference `em0023_001_02` and `em0011_001_03`. Both exist in `EnemyIndividualMasterData.json`. Neither is a matching episode `_id`; that is not, by itself, an error.

The episode enemy-detail response previously omitted generator-only targets: `em0011_001_03` was absent from its collected set for this episode. `fill_enemy_detail_by_episode_id` now collects placed, parent-child and summon individual IDs, removing duplicates and empty IDs while preserving first occurrence order. The server also publishes the global individual masters. Correcting the detail list does not prove that it explains every generator failure, especially barracks targeting the already included `em0023_001_02`.

Do not normalize zero summon limits without confirming their semantics. Some tower generators intentionally have `InitialAppearNum = 3`, `MinLimitNum = 0`, `TotalNum = 0`, `AppearPointName = "childpoint"`, and `DieWithChild = true`. Treating every zero total as “spawn nothing” would conflict with their nonzero initial count.

## Verification of the correction

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
| `EpisodeEnemyMasterData.Setup` | `0x3617FD0` | Calls external-definition creation only for debug-local boot |
| `EnemyManager.CreateEnemyChild` | `0x17D7E04` | Client child-creation entry point |
| `EnemyManager.CreateEnemySummon` | `0x17D7F78` | Starts the initial summon count through `CreateEnemyForSummon` |
| `EnemyManager.CreateEnemyForSummon` | `0x17D5C54` | Client summon creation path |

The C# dumps supply type contracts and method addresses; the parsing, lookup, and initial-summon observations above were checked against native instructions. The first barracks correction has been confirmed by a phone playtest. Other generators and resumed checkpoints still need separate gameplay checks.

Focused checks: `python -m unittest discover -s tests -p test_episode_enemies.py`. Set `EMBLEO_TEST_RAID_DATA` to the installed data directory to include Bastien-specific formation, summon-count and target-dependency checks. The fixture checks do not include extracted game data.

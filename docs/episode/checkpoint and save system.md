## Checkpoints

### Saving at checkpoint
When reaching a checkpoint with "RequestSave" set to True, the game pings `/api/episode/check-point` to save current progress.

Response from the server triggers "Connecting" and "Saving..." animation, however, the purple line with "Chapter X Y/ZZ" doesn't appear in the middle of the screen, which could mean that the progress is not saved properly.

### Starting episode from mid-way (checkpoint continue)
When episode is not started, there is Start button that pings `api/episode/start` with only episode_id.

After starting an episode and exiting it, episode tile should have "Continue" plack and the "Start" button should turn into "Continue" button. 

But where is this condition being stored? It is possible that if the game is saved properly, the game will automatically put the episode tile first, without server's involement.

### Retire
`api/episode/retire` triggers when you exit an episode through `Menu -> Take a Break -> Stop Playing`

## Chapters
Each episode is split into four chapters. After clearing an episode ("Status" = 1 or 2), you can select which of four chapters to start from with chapter buttons.

However, starting an episode through a chapter button sends only the episode ID and no other additional info that would let the server select appropriate position in the scenario.

There are constant values for chapter scenario numbers: 10000, 20000, 30000, 40000. Which roughly equates to how chapters are "split" in scenario files.

EpisodeMasterData has "Id" for each chapter, however it seems to be optional and also doesn't seem to affect episode's starting point.

Tested "Id" variants:
- Empty
- "CP_00001" (checkpoint id)
- "30000" (scenario number)
- "pl011_ep001_cp04" (chapter id like how audio is organised)

None seem to affect at which point episode starts.
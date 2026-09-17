Level Up Camp is handled separately from episodes by pinging `api/training-mission/` during loading.

To make Level Up Camp tile appear, add orderdId to user/top with MasterDataId - "LvUpCamp" and Type of 99 (Abstract).

To make levels selectable `api/training-mission/list` needs to be populated with three levels (from "exp_mission_001" to "exp_mission_006"). Adding more than three will confuse the game, but stages are interchangable and can be present in any order, not specifically 001-003 or 004-006.

Only one Level Up Camp tile can be present in the main menu.

Stage ID that is put into "LocationId" in TrainingMissions list is not the location that the game loads, but is used only for displaying the area name on the buttons.
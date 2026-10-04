import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from scripts.adapt import adapt_debug_episode_data as layouts
from scripts.adapt.episode_data.breakables import (
    adapt_breakables_for_episode_layout, adapt_breakable_items_for_episode_layout,
)


class EpisodeBreakableTests(unittest.TestCase):
    def setUp(self):
        self.source = {'Datas': [
            {'_id': object_id, '_masterID': 'breakable_0002',
             '_startScenarioNo': 30000, '_endScenarioNo': 39999,
             '_stackNum': 2, '_parallelNum': 1,
             '_dropLotteryID': 'gold_001', '_drops': []}
            for object_id in ('BOX_30005', 'BOX_30005a')
        ]}

    def test_breakable_records_use_only_network_fields(self):
        records = adapt_breakables_for_episode_layout(self.source)
        self.assertEqual(records, [
            {'EpisodeBreakableId': object_id, 'ResourceId': 'breakable_0002'}
            for object_id in ('BOX_30005', 'BOX_30005a')
        ])

    def test_items_supply_the_client_breakable_spawn_data(self):
        original = copy.deepcopy(self.source)
        records = adapt_breakable_items_for_episode_layout(self.source)
        self.assertEqual(records, [
            {'EpisodeItemId': object_id, 'ItemDropMethod': 2,
             'DropResourceId': 'breakable_0002', 'ObjectCount': 2,
             'ParallelNum': 1, 'EpisodeEvent': None,
             'ScenarioNo': [30000, 39999]}
            for object_id in ('BOX_30005', 'BOX_30005a')
        ])
        self.assertEqual(self.source, original)

    def test_layout_assembly_includes_items_without_other_episode_files(self):
        with patch.object(layouts.os, 'listdir', return_value=[
            'EpisodeBreakableMasterDataObject.json'
        ]), patch.object(layouts, 'load_json', return_value=self.source):
            result = layouts.fill_episode_layout_group_by_episode_id('fixture')
        self.assertEqual(result['Items'],
                         adapt_breakable_items_for_episode_layout(self.source))
        self.assertEqual(result['Breakables'],
                         adapt_breakables_for_episode_layout(self.source))
        self.assertEqual(result['StaticItems'], [])
        self.assertEqual(result['Enemies'], [])

    def test_preserves_zero_counts_and_distinct_scenario_ranges(self):
        source = {'Datas': [{
            '_id': 'disabled', '_masterID': 'breakable_0001',
            '_startScenarioNo': 40000, '_endScenarioNo': 49999,
            '_stackNum': 0, '_parallelNum': 3,
        }]}
        item = adapt_breakable_items_for_episode_layout(source)[0]
        self.assertEqual(item['ScenarioNo'], [40000, 49999])
        self.assertEqual(item['ObjectCount'], 0)
        self.assertEqual(item['ParallelNum'], 3)

    def test_empty_episode_has_no_breakables_or_items(self):
        self.assertEqual(adapt_breakables_for_episode_layout({'Datas': []}), [])
        self.assertEqual(adapt_breakable_items_for_episode_layout({'Datas': []}), [])


if __name__ == '__main__':
    unittest.main()

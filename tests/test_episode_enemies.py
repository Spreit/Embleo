import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from scripts.adapt import adapt_debug_episode_data as layouts
from scripts.adapt.episode_data.enemies import (
    adapt_episode_enemies_for_episode_layout, episode_enemy_individual_ids,
)


def enemy(role=1):
    return dict(_id='parent', _individualID='leader', _enemyType=role,
        _appearanceNum=1, _groupID='group', _appearanceID=1, _appearanceParam1=0, _appearanceIntParam1=0,
        _charactorVisualId='', _surviveId='', _patrolPoints=[], _priorityPoint='',
        _startScenarioNo=10000, _endScenarioNo=19999,
        _childEnemyData=dict(EnemyIds=['child', 'second'], FormationId='fixture'),
        _summonEnemyData=dict(EnemyId='summon-only', _initialAppearNum=3,
            _minLimitNum=0, _totalNum=0, Offset=dict(x=0,y=1), Range=dict(x=2,y=3),
            AppearPointName='childpoint', DieWithChild=1, InitRotateAngle=0,
            OffsetAdd=dict(x=4,y=5), RangeAdd=dict(x=6,y=7), InitRotateAngleAdd=8))


class EpisodeEnemyTests(unittest.TestCase):
    def setUp(self):
        self.source = {'Datas': [enemy()]}
        self.platoons = {'Datas': [dict(_id='fixture', Formation='1,0,2\r\n,1,',
                                      FormationPadding=dict(x=1.5,y=2))]}

    def test_parent_resolves_grid_padding_and_preserves_child_order(self):
        original = copy.deepcopy(self.source)
        row = adapt_episode_enemies_for_episode_layout(self.source,
            platoon_master_data=self.platoons)[0]
        self.assertEqual(row['Child'], dict(Ids=['child','second'],
            Formation='1,0,2\r\n,1,', FormationPadding=[1.5,2]))
        self.assertEqual(row['RoleType'], 2)
        self.assertEqual(self.source, original)

    def test_unknown_formation_is_reported_instead_of_publishing_lookup_id(self):
        with self.assertRaisesRegex(ValueError, "fixture.*parent"):
            adapt_episode_enemies_for_episode_layout(self.source,
                platoon_master_data={'Datas': []})

    def test_generator_and_normal_without_formation_keep_summon_semantics(self):
        for role in (0,2):
            entry = enemy(role)
            entry['_childEnemyData'] = dict(EnemyIds=[''],FormationId='')
            row = adapt_episode_enemies_for_episode_layout({'Datas':[entry]})[0]
            self.assertEqual(row['RoleType'],role+1)
            self.assertEqual(row['Child'],dict(Ids=[''],Formation='',FormationPadding=[0,0]))
            self.assertEqual(row['SummonRule']['EpisodeEnemyId'],'summon-only')
            self.assertEqual(row['SummonRule']['InitialAppearNum'],3)
            self.assertEqual(row['SummonRule']['TotalNum'],0)
            self.assertEqual(row['SummonRule']['AppearPointName'],'childpoint')
            self.assertTrue(row['SummonRule']['DieWithChild'])

    def test_enemy_detail_includes_summon_only_targets_without_empty_or_duplicate_ids(self):
        second = enemy()
        second['_individualID'] = 'child'
        second['_childEnemyData']['EnemyIds'] = ['', 'second']
        self.assertEqual(episode_enemy_individual_ids({'Datas':[enemy(),second]}),
                         ['leader','child','second','summon-only'])

    def test_layout_assembly_reads_shared_platoon_master(self):
        def load(path):
            if Path(path).name == 'PlatoonMasterDataObject.json':
                self.assertEqual(Path(path),Path('data/extract/masterdatadebug/PlatoonMasterDataObject.json'))
                return self.platoons
            return self.source
        with patch.object(layouts.os,'listdir',return_value=['EpisodeEnemyMasterDataObject.json']), patch.object(layouts,'load_json',side_effect=load):
            row = layouts.fill_episode_layout_group_by_episode_id('fixture')['Enemies'][0]
        self.assertEqual(row['Child']['FormationPadding'],[1.5,2])

    def test_release_child_definitions_are_external_and_keep_individual_identity(self):
        original = copy.deepcopy(self.source)
        rows = adapt_episode_enemies_for_episode_layout(self.source,platoon_master_data=self.platoons)
        self.assertEqual([r['EpisodeEnemyId'] for r in rows],
                         ['parent','Ext.parent.child','Ext.parent.second'])
        child = rows[1]
        self.assertEqual(child['EnemyId'],'child')
        self.assertEqual(child['RoleType'],1)
        self.assertEqual(child['AppearanceRule'],{'Type':2,'Params':[]})
        self.assertEqual(child['GroupId'],'group')
        self.assertEqual(child['ScenarioNo'],[10000,19999])
        self.assertEqual(child['AppearanceNum'],1)
        self.assertIsNone(child['Child'])
        self.assertIsNone(child['SummonRule'])
        self.assertEqual(self.source,original)

    def test_generator_emits_one_external_target_without_recursive_summon(self):
        entry = enemy(2)
        entry['_childEnemyData'] = dict(EnemyIds=[''],FormationId='')
        rows = adapt_episode_enemies_for_episode_layout({'Datas':[entry]})
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[1]['EpisodeEnemyId'],'Ext.parent.summon-only')
        self.assertEqual(rows[1]['EnemyId'],'summon-only')
        self.assertIsNone(rows[1]['SummonRule'])
        entry['_summonEnemyData']['EnemyId'] = ''
        self.assertEqual(len(adapt_episode_enemies_for_episode_layout({'Datas':[entry]})),1)

    def test_repeated_child_target_has_one_definition_and_id_collisions_fail(self):
        self.source['Datas'][0]['_childEnemyData']['EnemyIds']=['child','child']
        rows = adapt_episode_enemies_for_episode_layout(self.source,platoon_master_data=self.platoons)
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['Child']['Ids'],['child','child'])
        placed = enemy(0)
        placed['_id'] = 'Ext.parent.child'
        self.source['Datas'].append(placed)
        with self.assertRaisesRegex(ValueError,'Duplicate external episode enemy'):
            adapt_episode_enemies_for_episode_layout(self.source,platoon_master_data=self.platoons)

    @unittest.skipUnless(os.environ.get('EMBLEO_TEST_RAID_DATA'), 'installed data opt-in')
    def test_installed_bastien_first_part_children_and_generator_dependencies(self):
        root = Path(os.environ['EMBLEO_TEST_RAID_DATA'])
        extracted = root/'extract/masterdatadebug'
        source = json.loads((extracted/'episode/pl011_ep001/EpisodeEnemyMasterDataObject.json').read_text(encoding='utf-8'))
        platoons = json.loads((extracted/'PlatoonMasterDataObject.json').read_text(encoding='utf-8'))
        rows = adapt_episode_enemies_for_episode_layout(source,platoon_master_data=platoons)
        by_id = {row['EpisodeEnemyId']:row for row in rows}
        parent = by_id['EM_CP01_010-Platoon01']
        cells = [cell.strip() for line in parent['Child']['Formation'].splitlines() for cell in line.split(',') if cell.strip()]
        self.assertEqual(cells.count('1'),2)
        self.assertEqual(cells.count('0'),1)
        self.assertEqual(parent['Child']['Ids'],['em0023_001_02'])
        self.assertEqual(parent['Child']['FormationPadding'],[1,1])
        barracks = by_id['EM_CP01_001-Barracks01']['SummonRule']
        self.assertEqual((barracks['InitialAppearNum'],barracks['MinLimitNum'],barracks['TotalNum']),(15,15,25))
        external=by_id['Ext.EM_CP01_001-Barracks01.em0023_001_02']
        self.assertEqual(external['AppearanceRule']['Type'],2)
        self.assertEqual(external['EnemyId'],'em0023_001_02')
        self.assertIsNone(external['SummonRule'])
        individuals = json.loads((root/'masterdata/EnemyIndividualMasterData.json').read_text(encoding='utf-8'))
        known = {row['Index'] for row in individuals}
        self.assertFalse(set(episode_enemy_individual_ids(source))-known)
        self.assertIn('em0011_001_03',episode_enemy_individual_ids(source))
        self.assertTrue(all(row['Child']['Formation'] for row in rows if row['RoleType']==2))


if __name__ == '__main__':
    unittest.main()

import copy
from .indexed import put_clip, indexed_data


def normalize_IgnoreHitLayer(container):
    # Find and normalize recursively
    # to avoid specifying all IgnoreHitLayer positions
    if isinstance(container, list):
        return [normalize_IgnoreHitLayer(item) for item in container]

    if not isinstance(container, dict):
        return container

    result = {key: normalize_IgnoreHitLayer(item) for key, item in container.items()}
    mask = result.get('IgnoreHitLayer')
    if isinstance(mask, dict) and "m_Bits" in mask and "m_Mask" not in mask:
        bits = mask.pop('m_Bits')
        if isinstance(bits, int) and (0x80000000 <= bits <= 0xffffffff):
            bits -= 0x100000000
        mask['m_Mask'] = bits

    return result


ATTACK_CLIPS = {
    # Player attacks
    'Attack Clip': ('clip_Attack', 'attackClipSettings'),
    'GunAttack Clip': ('clip_Gun', 'gunAttackClipSettings'),
    'DeathBall Clip': ('clip_DeathBall', 'gunAttackClipSettings'),
    'Summon Clip': ('clip_Summon', 'clipSettings'),
    'LaserAttack Clip': ('clip_Laser', 'clipSettings'),
    'ThrowWeapon Clip': ('clip_ThrowWeapon', 'gunAttackClipSettings'),
    'HomingGun Clip': ('clip_HomingGun', 'gunAttackClipSettings'),
    'Charging Clip': ('clip_Charging', 'ChargingClipSettings'),
    'GrenadeAttack Clip': ('clip_Grenade', 'gunAttackClipSettings'),
    'PutShooting Clip': ('clip_PutShoot', 'gunAttackClipSettings'),
    'LookTargetGunAttack Clip': ('clip_LookGun', 'gunAttackClipSettings'),
    'Grenade PlungingFireAttack Clip': ('clip_Plunging', 'gunAttackClipSettings'),

    'MinionOrder Clip': ('clip_MinionOrder', 'minionOrderSettings'),
    'MinionAttack Clip': ('clip_MinionAttack', 'minionAttackClipSettings'),
    'RegisterBuff Clip': ('clip_RegisterBuff', 'clipSettings'),
    'AreaGuard Clip': ('clip_AreaGuard', 'clipSettings'),

    # Enemy Attacks
    'EnemyAttack Clip': ('enemy_Hit', '_hitParameter'),
    'EnemyColliderAttack Clip': ('enemy_ColliderHit', '_hitParameter'),
    'EnemyThrowGrabAttack Clip': ('enemy_Throw', '_grabParameter'),
    # LinkThrow?
    'EnemyLaserAttack Clip': ('enemy_Laser', '_laserParameter'),
    'EnemyCatchAttack Clip': ('enemy_CatchAttack', 'm_catchParam'),

    # Are EnemyHeal and EnemyRevive Clip suppose to be handled here?
    # em0111_01 and em0111_02 (Phoenix raid boss)
}

ATTACK_CLIPS_SKIP = {
    "RepairGauge Clip",
    "RevertWeapon Clip",  # Has no values at all
    "SkillActiveCharge Clip",  # August's Charge5, unrelated
    "ChargingRate By RemainGauge Clip",  # Lucien Charge5, unrelated
    "ResetCharge Clip",  # Celia Charge1, no values

    # Maxime, not meant to be parsed by this script
    "ResetTimeDecrease Clip",
    "TimeDecrease Clip",
    "Clear TimeDecrease EmptyTarget Clip",
    "BattleActionUI Clip",
    "BattleActionUI CheckTimeDecrease Clip",
    "PlayStateByTimeDecreaseParam Clip",

    # Lydie, not meant to be parsed by this script
    "InputChargeGauge Clip",
    "Setup InputChargeGauge Clip",
    "Reset InputChargeGauge Clip",
    "PlayStateByChargeParam Clip",

    # Charles
    "CreateMinionBit Clip",
    "MinionUnleash Clip",

    "EnemyHeal Clip",
    "EnemyRevive Clip"
}


def adapt_attack_track(attack_track, sequence_name, owner_id):
    AttackSetting = {
        "id": owner_id,
        "sequenceName": sequence_name,
        "baseInfo": None,
        "totalClipCount": 0,
        "clipCount": [],
        "clipDatas": []
    }

    clips = {}
    for clip in attack_track["clips"]:
        clip_MonoBehaviour = clip["behaviour"]
        clip_m_Name = clip_MonoBehaviour["m_Name"]
        # print(clip)

        # print()
        if clip_m_Name in ATTACK_CLIPS:
            destination_key, source_key = ATTACK_CLIPS[clip_m_Name]

            settings = clip_MonoBehaviour[source_key]
            index = settings.get('ClipIndex', clip_MonoBehaviour.get('clipIndex', len(clips)))
            attack_clip_setting = {destination_key: copy.deepcopy(settings)}
            if 'hitSettings' in clip_MonoBehaviour:
                attack_clip_setting['hitSetting'] = copy.deepcopy(clip_MonoBehaviour['hitSettings'])

            if clip_m_Name == "MinionAttack Clip":
                attack_clip_setting["clip_Attack"] = copy.deepcopy(clip_MonoBehaviour["attackClipSettings"])

            if clip_m_Name == "DeathBall Clip":
                attack_clip_setting["clip_DeathBall"] = copy.deepcopy(clip_MonoBehaviour["deathBallClipSettings"])

            if clip_m_Name == "EnemyThrowGrabAttack Clip":
                # print(clip_MonoBehaviour.keys())

                if "_throwAttackParameter" in clip_MonoBehaviour:
                    attack_clip_setting["enemy_Throw"] = copy.deepcopy(clip_MonoBehaviour["_throwAttackParameter"])

            attack_clip_setting = normalize_IgnoreHitLayer(attack_clip_setting)
            put_clip(clips, index, attack_clip_setting)

        elif clip_m_Name not in ATTACK_CLIPS_SKIP:
            print(owner_id, sequence_name, "-", clip_m_Name, "-", "Unknown attack clip")

    AttackSetting['clipDatas'] = indexed_data(clips)
    AttackSetting['totalClipCount'] = len(AttackSetting['clipDatas'])
    return AttackSetting

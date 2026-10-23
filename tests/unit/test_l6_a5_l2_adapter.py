import hashlib
import json

import pytest

from scripts.tw_market_installation import initialize_installation
from scripts.tw_market_l2_adapter import A1_COMPATIBILITY_CONTRACT, DeclaredInstallationMember, installation_backup_plan
from server.services.unified_backup import A1_SETTINGS_BINDING, BackupError, create_backup, verify_backup
from server.services.unified_restore import CompatibilityAttestation, restore_backup


def setup_plan(tmp_path):
    inst = initialize_installation(home=tmp_path/'source-home', environ={})
    member = DeclaredInstallationMember('preferences', 'settings', 'settings.json', 'user_product_settings',
                                       A1_SETTINGS_BINDING, hashlib.sha256(inst.settings_path.read_bytes()).hexdigest())
    return inst, member


def test_settings_transfer_uses_l2_and_preserves_destination_identity(tmp_path):
    source, member = setup_plan(tmp_path)
    dest = initialize_installation(home=tmp_path/'destination-home', environ={})
    metadata = dest.installation_metadata_path.read_bytes()
    plan = installation_backup_plan(source, members=(member,), backup_tier='CORE', max_total_bytes=10000)
    package = tmp_path/'backup'
    create_backup(plan, destination=package, backup_id='a5-core', created_at='2026-10-23T00:00:00Z')
    verify_backup(package, max_total_bytes=10000)
    manifest = json.loads((package/'backup-manifest.json').read_text())
    attestation = CompatibilityAttestation(manifest['manifest_integrity']['sha256'], {'preferences':'1'})
    result = restore_backup(backup_path=package, destination=tmp_path/'restored', compatibility=attestation,
                            contract=A1_COMPATIBILITY_CONTRACT, forbidden_roots=[source.home,dest.home],
                            max_total_bytes=10000,max_member_count=10,restore_id='a5-restore',created_at='2026-10-23T00:00:00Z')
    assert result['status']=='RESTORED_STATE_VERIFIED'
    assert (tmp_path/'restored/config/settings.json').read_bytes()==source.settings_path.read_bytes()
    assert dest.installation_metadata_path.read_bytes()==metadata
    assert dest.installation_id != source.installation_id
    assert manifest['source_state_identity']==source.installation_id
    assert not (tmp_path/'restored/meta').exists()


@pytest.mark.parametrize('extra', [{'home':'C:/source'}, {'secret':'private'}, {'service':{'host':'0.0.0.0','port':8000}}])
def test_settings_adapter_rejects_paths_unknown_fields_and_remote_listener(tmp_path, extra):
    source, member = setup_plan(tmp_path)
    data=json.loads(source.settings_path.read_text());data.update(extra)
    source.settings_path.write_text(json.dumps(data))
    with pytest.raises(BackupError,match='A1_PORTABLE_SETTINGS_INVALID'):
        installation_backup_plan(source,members=(member,),backup_tier='CORE',max_total_bytes=10000)


@pytest.mark.parametrize('role', ['installation_metadata','runtime','temp','logs','cache'])
def test_local_identity_and_ephemeral_roles_are_never_portable(tmp_path, role):
    source,_=setup_plan(tmp_path)
    member=DeclaredInstallationMember('local',role,'anything','user_product_settings',A1_SETTINGS_BINDING,'0'*64)
    with pytest.raises(ValueError,match='INSTALLATION_MEMBER_NOT_PORTABLE'):
        installation_backup_plan(source,members=(member,),backup_tier='CORE',max_total_bytes=10000)


def test_oversized_settings_are_rejected_before_json_parsing(tmp_path, monkeypatch):
    from server.services.unified_backup import validate_a1_portable_settings
    path = tmp_path/'oversized.json'
    with path.open('wb') as handle:
        handle.seek(2*1024*1024)
        handle.write(b' ')
    def forbidden_parse(*args, **kwargs):
        raise AssertionError('oversized settings reached JSON parser')
    monkeypatch.setattr(json, 'loads', forbidden_parse)
    with pytest.raises(BackupError, match='A1_PORTABLE_SETTINGS_INVALID'):
        validate_a1_portable_settings(path)

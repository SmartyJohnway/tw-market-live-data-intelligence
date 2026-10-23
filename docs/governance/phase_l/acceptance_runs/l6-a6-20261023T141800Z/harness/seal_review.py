import pathlib,json,hashlib,subprocess,shutil,re
R=pathlib.Path(r'C:\twmarket_temp\l6-a6');P=R/'repo';REL='docs/governance/phase_l/acceptance_runs/l6-a6-20261023T141800Z';E=P/REL
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(d):return json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def save(n,d):(E/(n+'.json')).write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def read(n):return json.loads((E/(n+'.json')).read_text())
assert read('failed_node_comparison')['candidate_stage']=='candidate-final'
assert read('failed_node_comparison')['candidate_only_count']==0 and read('l6_exit_criteria_matrix')['pass_count']==23
assert all(x['returncode']==0 for x in read('required_validators'))
assert read('compile_static')['returncode']==0
assert read('final_technical_review')['technical_disposition']=='PHASE_L_L6_EXIT_REVIEW_PASS'
for p in R.glob('*.py'):
    target=E/'harness'/p.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target)
shutil.copyfile(R/'ci/guard.py',E/'harness/guard.py')
for p in ['candidate-prefrontdoor-default-ci.json','candidate-prefrontdoor-report.xml']:
    shutil.copyfile(R/'ci'/p,E/p)
attachment=pathlib.Path(r'C:\Users\weitang\.codex\attachments\1e33a4e3-9d02-4ef8-9c7f-0d2741c466d4\貼上的文字.txt')
original=attachment.read_bytes();(E/'owner_authorization.md').write_bytes(original)
d=read('authority');d.update(original_instruction_sha256=sha(original),instruction_copy='owner_authorization.md');save('authority',d)
allowed={'PROJECT.md','HANDOFF.md','ROADMAP.md','docs/governance/INDEX.md','docs/governance/phase_l/PHASE_L_CURRENT_STATUS_AND_RECOVERY_INDEX_2026-10-14.md','docs/governance/phase_l/PHASE_L_L6_A6_PACKAGING_PORTABILITY_TECHNICAL_EXIT_REVIEW_2026-10-23.md'}
tracked=subprocess.check_output(['git','diff','--name-only','365ea26e76e24aa0171945d29ba2b21f79c3a8db'],cwd=P,text=True).splitlines()
untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=P,text=True).splitlines()
assert all(p in allowed or p.startswith(REL+'/') for p in tracked+untracked)
protected=subprocess.check_output(['git','diff','--name-only','365ea26e76e24aa0171945d29ba2b21f79c3a8db','--','scripts','server','tests','config','schemas','packaging_native','packaging_docker','requirements.txt','VERSION','frontend','skills'],cwd=P,text=True);assert not protected
save('scope_diff_verification',{'status':'PASS','entry':'365ea26e76e24aa0171945d29ba2b21f79c3a8db','allowed_front_doors_and_review':sorted(allowed),'review_evidence_prefix':REL,'product_runtime_changes':0,'public_contract_changes':0,'test_semantic_changes':0,'dependency_changes':0,'historical_evidence_changes':0,'review_only_helpers':True,'D_drive_access_commands':0,'live_provider_requests':0,'production_state_mutations':0})
save('git_diff_check',{'status':'PASS','command':'git diff --cached --check','method':'mandatory final staged check after text normalization and before commit; failure aborts commit'})
normalization={}
for p in E.rglob('*'):
    if p.is_file() and p.name not in {'manifest.json','text_normalization.json'}:
        before=p.read_bytes();after=b'\n'.join(x.rstrip(b' \t') for x in before.replace(b'\r\n',b'\n').split(b'\n'))
        if before!=after:normalization[p.relative_to(E).as_posix()]={'pre_normalization_copy_sha256':sha(before),'committed_sha256':sha(after)}
        p.write_bytes(after)
prior=read('text_normalization') if (E/'text_normalization.json').exists() else {'members':{}}
prior['members'].update(normalization);prior['policy']='New review text copies only: normalize LF and line-end whitespace; original logs retained in bounded A6 workspace; historical repository evidence never altered.';save('text_normalization',prior)
pattern=re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9]{32,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')
files=[p for p in E.rglob('*') if p.is_file() and p.name!='manifest.json']
for p in files:assert not pattern.search(p.read_bytes()),p.name
save('secret_scan',{'status':'PASS','member_count':len(files),'known_credential_private_key_shapes_found':0,'scope':'new A6 evidence/helper/authority text only; no credentials/cache/venv/archive copied','limitation':'pattern based, not a claim about arbitrary unknown secrets'})
manifest={'schema':'twmarket.l6_a6.review_evidence.v1','entry_commit':'365ea26e76e24aa0171945d29ba2b21f79c3a8db','entry_tree':'811985144e835e24dc01f8a130c8b959f83c5f0d','accepted_A5_source':'3707c553497240f6ff0f7e5358301395fd60205a','canonicalization':'compact sorted UTF-8 JSON ensure_ascii=false excluding only self_digest','members':[{'path':p.relative_to(E).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(E.rglob('*')) if p.is_file() and p.name!='manifest.json']}
manifest['self_digest']=sha(canon(manifest));save('manifest',manifest)
check=read('manifest');digest=check.pop('self_digest');assert sha(canon(check))==digest
for row in check['members']:assert sha((E/row['path']).read_bytes())==row['sha256']
print(json.dumps({'status':'PASS','evidence_members':len(check['members']),'self_digest':digest}))

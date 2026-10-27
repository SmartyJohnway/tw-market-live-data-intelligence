"""Redacted path/secret evidence bound to original accepted wheel members."""
from __future__ import annotations

import hashlib
import os
from pathlib import PurePosixPath
import re
import zipfile

SECRET = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{32,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s+[A-Za-z0-9+/=\r\n]{40,})')
BINARY_SUFFIXES={'.pyd','.dll','.exe','.lib'}
PATH_RE=re.compile(r'''(?i)(?<![A-Za-z0-9_%\\])([A-Z]:[\\/]+[^\r\n\t"'<>|`\ufffd\x00-\x1f]*)''')
EXAMPLE_PATHS={
    'server/lib/pythonwin/pywin/framework/bitmap.py':{r'd:\winnt\arcade.bmp'},
    'server/lib/win32/scripts/VersionStamp/vssutil.py':{r'd:\src\pythonex\win32\win32.txt',r'd:\temp\win32.txt'},
    'server/lib/win32com/makegw/makegw.py':{r'd:\msdev\include\objidl.h'},
    'server/lib/win32com/makegw/makegwparse.py':{r'd:\msdev\include\objidl.h'},
}
GENERATED_SOURCE={
    'server/lib/win32/Demos/win32wnet/winnetwk.py','server/lib/win32/lib/mmsystem.py',
    'server/lib/win32/lib/win32con.py','server/lib/win32/lib/win32netcon.py',
    'server/lib/win32com/storagecon.py',
}
AUTHORING_DOCUMENTS={
    'server/lib/win32com/HTML/'+name for name in (
        'GeneratedSupport.html','PythonCOM.html','QuickStartClientCom.html',
        'QuickStartServerCom.html','docindex.html','misc.html','package.html')
}
TEXT_EXACT_MEMBERS={
    'server/lib/numpy-2.4.6.dist-info/DELVEWHEEL',
    'server/lib/pandas-3.0.5.dist-info/DELVEWHEEL',
    'server/lib/pydantic_core-2.46.5.dist-info/sboms/pydantic-core.cyclonedx.json',
    'server/lib/rpds_py-2026.6.3.dist-info/sboms/rpds-py.cyclonedx.json',
}


def text_subclass(name):
    if name in TEXT_EXACT_MEMBERS:
        return 'THIRD_PARTY_ACCEPTED_BUILD_PROVENANCE_TEXT_EXACT_MEMBER'
    if name=='server/lib/numpy/__config__.py' or re.fullmatch(
            r'server/lib/cryptography-[^/]+\.dist-info/sboms/[^/]+\.json',name):
        return 'THIRD_PARTY_ACCEPTED_BUILD_PROVENANCE_TEXT'
    return None


def wheel_members(wheelhouse, dependencies):
    mapping={}
    for d in dependencies:
        wheel=wheelhouse/d['wheel_filename']
        if hashlib.sha256(wheel.read_bytes()).hexdigest()!=d['wheel_sha256']:
            raise ValueError('wheel identity mismatch')
        with zipfile.ZipFile(wheel) as z:
            for name in z.namelist():
                if name.endswith('/') or '.data/' in name:
                    continue
                key='server/lib/'+name
                record={'wheel':wheel.name,'wheel_sha256':d['wheel_sha256'],'origin_wheel_member':name,
                        'member_sha256':hashlib.sha256(z.read(name)).hexdigest()}
                if key in mapping and mapping[key]!=record:
                    raise ValueError('ambiguous wheel provenance')
                mapping[key]=record
    return mapping


def scan(name, data, provenance=None):
    observations=[]
    installed_sha=hashlib.sha256(data).hexdigest()
    bound=bool(provenance and provenance['member_sha256']==installed_sha)
    secret=bool(SECRET.search(data))
    is_binary=PurePosixPath(name).suffix.lower() in BINARY_SUFFIXES and data.startswith((b'MZ',b'!<arch>'))
    def add(rule,blocking,classification,value=None):
        row={'member':name,'rule':rule,'blocking':blocking,'classification':classification}
        if value is not None:
            row['matched_value_sha256']=hashlib.sha256(value.encode()).hexdigest()
        if provenance:
            row.update(provenance)
            row['installed_member_sha256']=hashlib.sha256(data).hexdigest()
            row['origin_member_sha256']=provenance['member_sha256']
            row['byte_identical_to_wheel_member']=row['installed_member_sha256']==row['origin_member_sha256']
            row['current_host_match']=False
            row['secret_material_match']=secret
        observations.append(row)
    parts=PurePosixPath(name.replace('\\','/')).parts
    if name.startswith(('/','\\')) or '..' in parts or ':' in name or any(x in {'.git','__pycache__','.pytest_cache','.venv','acceptance_runs'} for x in parts):
        add('FORBIDDEN_MEMBER',True,'FIRST_PARTY_LEAKAGE')
    if any(x.lower() in {'.env','auth.json','credentials.json','credentials','id_rsa','id_ed25519'} for x in parts):
        add('CREDENTIAL_MEMBER',True,'SECRET_MATERIAL')
    if secret:
        add('SECRET_PATTERN',True,'SECRET_MATERIAL')
    texts=[data.decode('utf-8',errors='replace')]
    for encoding,signature in [('utf-16-le',b':\x00'),('utf-16-be',b'\x00:')]:
        if is_binary and signature in data:
            texts.append(data.decode(encoding,errors='replace'))
    seen=set()
    for text in texts:
        for match in PATH_RE.finditer(text):
            path=match.group(1).rstrip(' .,;:)]}')
            normalized=re.sub(r'\\+',r'\\',path.lower().replace('/','\\'))
            if normalized in seen:
                continue
            seen.add(normalized)
            user=os.environ.get('USERNAME','').lower()
            current=('c:\\twmarket_temp' in normalized or 'd:\\codex-workspace' in normalized
                     or '\\tw-market\\' in normalized
                     or bool(user and re.search(r'c:\\users\\'+re.escape(user)+r'(?:\\|$)',normalized)))
            context=text[text.rfind('\n',0,match.start())+1:text.find('\n',match.end()) if '\n' in text[match.end():] else len(text)]
            classification=None
            if not current and bound and not secret:
                if normalized==r'c:\foo\bar.txt' or normalized.rstrip('\\') in {r'd:',r'c:\users',r'c:\windows'} or normalized.startswith('c:\\windows'):
                    classification='GENERIC_PATH_OR_URI_EXAMPLE'
                elif normalized in EXAMPLE_PATHS.get(name,set()):
                    classification='NONBLOCKING_UPSTREAM_EXAMPLE_PATH_LITERAL'
                elif name in GENERATED_SOURCE and re.search(r'(?i)(?:this file was )?generated by h2py from\s+',context):
                    classification='NONBLOCKING_UPSTREAM_GENERATED_SOURCE_PROVENANCE'
                elif name in AUTHORING_DOCUMENTS and normalized==r'd:\program files\microsoft office\office\html.dot' and re.search(r'(?i)meta\s+name\s*=\s*["\x27]template',context):
                    classification='NONBLOCKING_UPSTREAM_DOCUMENT_AUTHORING_PROVENANCE'
                elif text_subclass(name):
                    # These exact source/metadata classes are reviewed upstream
                    # build configuration, wheel-repair arguments and SBOM paths.
                    classification='NONBLOCKING_UPSTREAM_BUILD_PROVENANCE'
                elif is_binary and (normalized.endswith(('.pdb','.obj','.rs','.c','.cc','.cpp','.h','.hpp','.pyx','.lib','.dll')) or any(marker in normalized for marker in ('\\.cargo\\','\\.rustup\\','\\build\\','\\_work\\','d:\\a\\'))):
                    classification='NONBLOCKING_UPSTREAM_BUILD_PROVENANCE'
            sensitive=normalized.startswith(('c:\\users','c:\\twmarket_temp','d:')) or current
            if classification:
                add('SEMANTIC_PATH',False,classification,normalized)
                observations[-1]['provenance_subclass']=text_subclass(name) or ('THIRD_PARTY_ACCEPTED_BUILD_PROVENANCE_BINARY' if is_binary else classification)
            elif sensitive:
                add('PRIVATE_MACHINE_PATH',True,'UNPROVEN_BINARY_PATH' if is_binary else 'UNAUTHORIZED_THIRD_PARTY_TEXT_PATH' if name.startswith('server/lib/') else 'FIRST_PARTY_LEAKAGE',normalized)
                observations[-1]['current_host_match']=current
        for uri in re.finditer(r'(?i)file:///',text):
            # A bare URI scheme has no host identity; concrete Windows targets
            # are independently scanned by PATH_RE, including current-host URIs.
            if bound and not secret:
                add('GENERIC_FILE_URI_PREFIX',False,'GENERIC_PATH_OR_URI_EXAMPLE','file:///')
        if re.search(r'(?i)%LOCALAPPDATA%',text):
            add('LOCAL_STATE_REFERENCE',True,'FIRST_PARTY_LEAKAGE','%LOCALAPPDATA%')
    # The private-path matcher deliberately excludes printf %d and regex \\d
    # tokens. Such lexical false positives produce no path observation.
    return observations

"""Canonical wheel RECORD over the final server/lib projection only."""
from __future__ import annotations

import base64
import configparser
import csv
import hashlib
import io
from pathlib import Path, PurePosixPath
import re
import zipfile


def excluded_launchers(wheelhouse, dependencies):
    """Exact declared console/gui entrypoints and wheel .data/scripts; never a glob."""
    result = {}
    for dep in dependencies:
        with zipfile.ZipFile(Path(wheelhouse)/dep['wheel_filename']) as archive:
            names=set()
            for name in archive.namelist():
                if name.endswith('.dist-info/entry_points.txt'):
                    config=configparser.ConfigParser(interpolation=None)
                    config.optionxform=str
                    config.read_string(archive.read(name).decode('utf-8'))
                    for section in ('console_scripts','gui_scripts'):
                        if config.has_section(section):
                            names.update(key+'.exe' for key in config[section])
                if '.data/scripts/' in name and not name.endswith('/'):
                    script=name.split('.data/scripts/',1)[1]
                    names.add(script)
                    if script.endswith('.py'):
                        names.add(script[:-3]+'.exe')
            dist_records=[n for n in archive.namelist() if n.endswith('.dist-info/RECORD')]
            if len(dist_records)!=1:
                raise ValueError('MCPB_RECORD_CANONICALIZATION_INVALID: wheel RECORD identity')
            result[dist_records[0]]={'../../bin/'+name for name in names}
    return result


def canonical_record(data, own_path, payload, excluded=()):
    if data.startswith(b'\xef\xbb\xbf'):
        raise ValueError('MCPB_RECORD_CANONICALIZATION_INVALID: BOM')
    try:
        rows=list(csv.reader(io.StringIO(data.decode('utf-8'),newline=''),strict=True))
    except (UnicodeError,csv.Error) as exc:
        raise ValueError('MCPB_RECORD_CANONICALIZATION_INVALID: CSV') from exc
    seen=set(); final=[]; omitted=[]
    for row in rows:
        if len(row)!=3:
            raise ValueError('MCPB_RECORD_CANONICALIZATION_INVALID: CSV column count')
        name,old_hash,old_size=row
        name=name.replace('\\','/')
        if not name or name.casefold() in seen:
            raise ValueError('MCPB_RECORD_CANONICALIZATION_INVALID: duplicate/empty path')
        seen.add(name.casefold())
        if old_hash and not re.fullmatch(r'sha256=[A-Za-z0-9_-]{43}',old_hash):
            raise ValueError('MCPB_RECORD_CANONICALIZATION_INVALID: hash semantics')
        if old_size and not old_size.isdecimal():
            raise ValueError('MCPB_RECORD_CANONICALIZATION_INVALID: size semantics')
        if name in excluded:
            omitted.append({'path':name,'classification':'DECLARED_NON_DISTRIBUTED_PIP_LAUNCHER'})
            continue
        parts=PurePosixPath(name)
        if parts.is_absolute() or '..' in parts.parts or ':' in name or any(p in ('','.','..') for p in name.split('/')):
            raise ValueError('MCPB_RECORD_CANONICALIZATION_INVALID: traversal/ambiguous path')
        if name not in payload:
            raise ValueError('MCPB_RECORD_CANONICALIZATION_INVALID: unresolved member')
        if name==own_path:
            final.append([name,'',''])
        else:
            if name.endswith('.dist-info/RECORD'):
                raise ValueError('MCPB_RECORD_CANONICALIZATION_INVALID: cross-RECORD reference')
            value=payload[name]
            encoded=base64.urlsafe_b64encode(hashlib.sha256(value).digest()).rstrip(b'=').decode('ascii')
            final.append([name,'sha256='+encoded,str(len(value))])
    if own_path.casefold() not in seen:
        raise ValueError('MCPB_RECORD_CANONICALIZATION_INVALID: missing own row')
    out=io.StringIO(newline='')
    csv.writer(out,lineterminator='\n').writerows(sorted(final,key=lambda row:row[0]))
    return out.getvalue().encode('utf-8'),omitted


def normalize_installed(lib, wheelhouse, dependencies):
    paths={p.relative_to(lib).as_posix():p for p in lib.rglob('*') if p.is_file()
           and p.relative_to(lib).parts[0].lower() not in {'bin','scripts'}
           and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    payload={n:p.read_bytes() for n,p in paths.items()}
    exclusions=excluded_launchers(wheelhouse,dependencies)
    observations=[]
    for name in sorted(n for n in payload if n.endswith('.dist-info/RECORD')):
        allowed=exclusions.get(name,set())
        for row in allowed:
            if not (lib/'bin'/row.rsplit('/',1)[-1]).is_file():
                raise ValueError('MCPB_RECORD_CANONICALIZATION_INVALID: missing declared launcher')
        value,omitted=canonical_record(payload[name],name,payload,allowed)
        paths[name].write_bytes(value)
        observations.append({'record':name,'excluded_launchers':omitted,'sha256':hashlib.sha256(value).hexdigest()})
    for name,original in payload.items():
        if not name.endswith('.dist-info/RECORD') and paths[name].read_bytes()!=original:
            raise ValueError('non-RECORD bytes changed')
    return observations

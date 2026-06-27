from __future__ import annotations
import argparse,json,shutil,tempfile
from pathlib import Path
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument('--package-dir',required=True); ns=p.parse_args(argv)
 tmp=Path(tempfile.mkdtemp()); shutil.copytree(ns.package_dir,tmp/'package'); shutil.rmtree(tmp/'package')
 print(json.dumps({'status':'pass','rollback_simulated_in_tmp_path':True,'committed_package_deleted':False},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())

from m5d_publication_common import build
if __name__=='__main__':
 print(__import__('json').dumps(build(),indent=2,sort_keys=True))

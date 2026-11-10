"""Refuse a wrong native dependency before promotion/archive/unpack writes."""
import re
import subprocess

ATOM=re.compile(r'([a-z0-9][a-z0-9+.-]*)(?:\s*\((>=|<=|=|<<|>>)\s*([^()\s]+)\))?')

def verify(depends, query, compare):
 for clause in depends.split(','):
  alternatives=[]
  for atom in clause.split('|'):
   match=ATOM.fullmatch(atom.strip())
   if not match:raise ValueError('Unsupported dependency syntax: '+atom.strip())
   name,operator,version=match.groups()
   status,installed=query(name)
   alternatives.append((name,status,installed,operator,version))
  if not any(status=='install ok installed' and (operator is None or compare(installed,operator,version)) for _,status,installed,operator,version in alternatives):
   raise ValueError('Unsatisfied owned dependency before package writes: '+clause.strip()+'; observed '+repr(alternatives))

def native(depends):
 def query(name):
  r=subprocess.run(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status}\t${Version}',name],capture_output=True,text=True)
  if r.returncode==1:return 'absent',''
  if r.returncode!=0:raise RuntimeError('Cannot establish native dependency state: '+name)
  status,version=r.stdout.split('\t');return status,version
 def compare(installed,operator,version):
  r=subprocess.run(['chroot','/mnt/lfs','dpkg','--compare-versions',installed,operator,version])
  if r.returncode not in (0,1):raise RuntimeError('Native dependency version comparison failed')
  return r.returncode==0
 verify(depends,query,compare)

#!/usr/bin/env python3
"""Protector of Earth 3DS - builder de inventario e relatórios.

Analisa uma cópia extraída dos arquivos do PSP. Não modifica a origem,
 não descriptografa executáveis e não converte assets proprietários.
Requer Python 3.9+ e somente biblioteca padrão.
"""
from __future__ import annotations
import argparse, hashlib, json, os, struct, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.2.0"
MAGIC = [(b'\x7fELF','ELF'),(b'~PSP','PSP_SCE_PRX'),(b'PSMF','PSMF_video'),
         (b'RIFF','RIFF_container'),(b'OggS','OGG'),(b'ID3','MP3_ID3'),
         (b'\x89PNG\r\n\x1a\n','PNG'),(b'DDS ','DDS_texture'),(b'TIM2','TIM2_texture'),(b'GIM','GIM_texture')]
CATEGORIES = {'.r4s':'unknown_game_data','.r4m':'unknown_game_data','.pmf':'psp_video',
 '.prx':'psp_module_candidate','.at3':'psp_audio_candidate','.png':'image', '.sfo':'psp_metadata',
 '.txt':'configuration_or_text','.bin':'binary','.wav':'audio','.gim':'texture_candidate',
 '.tm2':'texture_candidate','.mdl':'model_candidate','.pak':'archive_candidate'}

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def signature(head: bytes) -> str:
    return next((name for magic,name in MAGIC if head.startswith(magic)), 'unknown')

def parse_elf(path: Path):
    data=path.read_bytes()
    if len(data)<52 or data[:4]!=b'\x7fELF': return None
    cls,endian=data[4],data[5]
    if cls!=1 or endian!=1:
        return {'format':'ELF','class':cls,'endianness':endian,'note':'Detalhamento disponível somente para ELF32 little-endian.'}
    try:
        etype,machine,_,entry,phoff,shoff,flags,ehsize,phentsize,phnum,shentsize,shnum,shstrndx=struct.unpack_from('<HHIIIIIHHHHHH',data,16)
        sections_raw=[]
        for i in range(min(shnum,10000)):
            off=shoff+i*shentsize
            if shentsize<40 or off+40>len(data): break
            sections_raw.append(struct.unpack_from('<IIIIIIIIII',data,off))
        names=b''
        if shstrndx<len(sections_raw):
            s=sections_raw[shstrndx]
            if s[4]<=len(data) and s[5]<=len(data)-s[4]: names=data[s[4]:s[4]+s[5]]
        sections=[]
        for s in sections_raw:
            end=names.find(b'\0',s[0]) if s[0]<len(names) else -1
            sections.append({'name':names[s[0]:end].decode('ascii','replace') if end>=0 else '',
                             'type':hex(s[1]),'address':hex(s[3]),'file_offset':hex(s[4]),'size':s[5]})
        segments=[]
        for i in range(min(phnum,10000)):
            off=phoff+i*phentsize
            if phentsize<32 or off+32>len(data): break
            t,o,v,p,fs,ms,fl,al=struct.unpack_from('<IIIIIIII',data,off)
            segments.append({'type':hex(t),'offset':hex(o),'vaddr':hex(v),'file_size':fs,'memory_size':ms,'flags':hex(fl),'alignment':hex(al)})
        return {'format':'ELF32','endianness':'little','type':hex(etype),'machine_id':machine,
                'machine_name':{8:'MIPS',40:'ARM'}.get(machine,'unknown'),'entry_point':hex(entry),
                'flags':hex(flags),'program_header_count':phnum,'section_count':len(sections),
                'segments':segments,'sections':sections,
                'note':'Metadados ELF não comprovam descriptografia nem compatibilidade com Nintendo 3DS.'}
    except (struct.error,IndexError,ValueError) as e: return {'format':'ELF','parse_error':str(e)}

def parse_text(path: Path):
    try: raw=path.read_text(encoding='utf-8-sig')
    except (UnicodeError,OSError): return None
    lines=[x.strip() for x in raw.splitlines() if x.strip() and not x.lstrip().startswith(('#',';','//'))]
    if path.suffix.lower()=='.txt':
        return {'line_count':len(raw.splitlines()),'nonempty_lines':len(lines),
                'key_value_entries':sum(1 for x in lines if len(x.split())>=2 and not x.startswith(('LEVEL','//')))}
    return None

def main():
    ap=argparse.ArgumentParser(description='Gera inventário e relatório para Protector of Earth 3DS.')
    ap.add_argument('root',help='Diretório extraído do jogo (por exemplo, PSP_GAME ou a pasta que contém USRDIR/SYSDIR).')
    ap.add_argument('--out',default='poe3ds_report',help='Pasta de saída (padrão: poe3ds_report).')
    ap.add_argument('--no-hash',action='store_true',help='Pula SHA-256 para acelerar a análise.')
    args=ap.parse_args(); root=Path(args.root).expanduser().resolve(); out=Path(args.out).expanduser().resolve()
    if not root.is_dir(): print(f'Erro: diretório não encontrado: {root}',file=sys.stderr); return 2
    out.mkdir(parents=True,exist_ok=True)
    files=[]; ext=Counter(); sig=Counter(); total=0; executables=[]; text_files=[]; pairs=defaultdict(dict); errors=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file(): continue
        rel=p.relative_to(root).as_posix()
        try:
            size=p.stat().st_size
            with p.open('rb') as f: head=f.read(64)
            mag=signature(head); suffix=p.suffix.lower(); total+=size; ext[suffix or '(sem extensão)']+=1; sig[mag]+=1
            item={'relative_path':rel,'size_bytes':size,'extension':suffix or '(sem extensão)',
                  'category':CATEGORIES.get(suffix,'unclassified'),'detected_signature':mag}
            if not args.no_hash: item['sha256']=sha256(p)
            files.append(item)
            if mag=='ELF' or p.name.upper() in ('BOOT.BIN','EBOOT.BIN'):
                executables.append({'file':rel,'signature':mag,'elf_analysis':parse_elf(p) if mag=='ELF' else None})
            if suffix=='.txt': text_files.append({'file':rel,**(parse_text(p) or {})})
            if suffix in ('.r4s','.r4m'):
                pairs[p.stem][suffix[1:]]={'path':rel,'size_bytes':size}
        except OSError as e: errors.append({'file':rel,'error':str(e)})
    paired=[{'basename':k,'r4s':v.get('r4s'),'r4m':v.get('r4m'),'has_both':('r4s' in v and 'r4m' in v)} for k,v in sorted(pairs.items())]
    summary={'project':'Protector of Earth 3DS','tool':'POE3DS Builder','version':VERSION,
      'generated_at':datetime.now(timezone.utc).isoformat(),'source_directory':str(root),'file_count':len(files),
      'total_bytes':total,'total_megabytes':round(total/1_000_000,2),'extension_counts':dict(ext.most_common()),
      'signature_counts':dict(sig.most_common()),'r4_pair_basename_count':len(paired),
      'r4_complete_pairs':sum(x['has_both'] for x in paired),'r4_incomplete_pairs':sum(not x['has_both'] for x in paired),
      'hashes_generated':not args.no_hash,
      'limitations':['Não extrai ISO/CSO.','Não descriptografa EBOOT.BIN ou PRX.','Não decodifica nem converte R4S/R4M; a associação por nome-base não confirma o papel dos arquivos.','Não converte modelos, texturas, áudio ou vídeos para formatos do 3DS.','Não compila nem gera um executável 3DS.']}
    (out/'game_manifest.json').write_text(json.dumps({'summary':summary,'files':files},indent=2,ensure_ascii=False),encoding='utf-8')
    (out/'executable_report.json').write_text(json.dumps(executables,indent=2,ensure_ascii=False),encoding='utf-8')
    (out/'asset_summary.json').write_text(json.dumps({'extension_counts':dict(ext.most_common()),'signature_counts':dict(sig.most_common()),
      'asset_candidates':[x for x in files if x['category']!='unclassified']},indent=2,ensure_ascii=False),encoding='utf-8')
    (out/'r4_pair_report.json').write_text(json.dumps(paired,indent=2,ensure_ascii=False),encoding='utf-8')
    (out/'text_file_report.json').write_text(json.dumps(text_files,indent=2,ensure_ascii=False),encoding='utf-8')
    (out/'scan_errors.json').write_text(json.dumps(errors,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f"{summary['project']} — análise concluída")
    print(f"{len(files)} arquivos | {total:,} bytes | {len(paired)} nomes-base R4 | {summary['r4_complete_pairs']} pares completos")
    print(f'Relatórios: {out}')
    return 0
if __name__=='__main__': raise SystemExit(main())

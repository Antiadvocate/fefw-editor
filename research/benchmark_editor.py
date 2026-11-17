"""Measure save-reader work (not Tk rendering); accepts private saves locally."""
from pathlib import Path
import argparse,hashlib,json,statistics,sys,time


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('saves',nargs='+',type=Path)
    ap.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--repeat',type=int,default=5)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    if args.repeat<1:ap.error('--repeat must be positive')
    sys.path.insert(0,str(args.source.resolve()))
    import fefw_core as core,fefw_save as container
    import facilities,facility_access,tutorials,blessings,fast_travel,deeds,boons,worldmap,story,story_start
    readers=(core.flag_maps,worldmap.read,tutorials.read,blessings.read,fast_travel.read,
             facilities.read,facility_access.report,deeds.read,boons.read_state,story.read)
    def panels(f):
        out=[]
        for fn in readers:
            try:out.append(fn(f))
            except core.SaveError as e:out.append((type(e).__name__,str(e)))
        return out
    result=[]
    for index,path in enumerate(args.saves):
        box=container.SaveFile(str(path));f=core.SaveFile(box.payload);original=bytes(f.payload)
        warm=panels(f)
        workloads={'panel_reads_cold':lambda:panels(core.SaveFile(original)),
                   'panel_reads_warm':lambda:panels(f),
                   'functions_warm':lambda:(facilities.read(f),facility_access.report(f)),
                   'chapter_entry':lambda:story_start.edited(f,9)}
        values={}
        for name,fn in workloads.items():
            times=[]
            for _ in range(args.repeat):
                t=time.perf_counter();fn();times.append(time.perf_counter()-t)
            values[name]={'median_seconds':statistics.median(times),'seconds':times}
        assert bytes(f.payload)==original
        result.append({'sample':index,'payload_bytes':len(original),'timings':values,
                       'read_digest':hashlib.sha256(repr(warm).encode()).hexdigest(),
                       'entry_digest':hashlib.sha256(story_start.edited(f,9)).hexdigest()})
    args.output.write_text(json.dumps({'note':'Data processing only; excludes Tk drawing and file writes.',
                                     'repeat':args.repeat,'results':result},indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()

import subprocess,tempfile,glob,shutil
from pathlib import Path
from flask import Flask,request,jsonify,Response
app=Flask(__name__); MAX_BYTES=20*1024*1024
@app.get("/health")
def health():
    exe=shutil.which("Audiveris") or shutil.which("audiveris") or "/opt/audiveris/bin/Audiveris"
    return jsonify({"ok":Path(exe).exists() or shutil.which(exe) is not None,"engine":"Audiveris"})
@app.post("/v1/recognize")
def recognize():
    f=request.files.get("file")
    if not f:return jsonify({"error":"file field is required"}),400
    data=f.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES:return jsonify({"error":"file too large"}),413
    suffix=Path(f.filename or "score.pdf").suffix.lower()
    if suffix not in {".pdf",".png",".jpg",".jpeg"}:return jsonify({"error":"unsupported type"}),415
    with tempfile.TemporaryDirectory() as td:
        src=Path(td)/("input"+suffix);src.write_bytes(data);out=Path(td)/"out";out.mkdir()
        exe=shutil.which("Audiveris") or shutil.which("audiveris") or "/opt/audiveris/bin/Audiveris"
        try:p=subprocess.run([exe,"-batch","-export","-output",str(out),str(src)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=110)
        except subprocess.TimeoutExpired:return jsonify({"error":"recognition timeout"}),504
        except Exception as e:return jsonify({"error":"Audiveris unavailable","detail":str(e)}),503
        found=list(out.rglob("*.mxl"))+list(out.rglob("*.musicxml"))+list(out.rglob("*.xml"))
        if p.returncode!=0 or not found:return jsonify({"error":"recognition failed","log":p.stdout.decode("utf-8","ignore")[-3000:]}),422
        result=found[0]; mime="application/vnd.recordare.musicxml" if result.suffix==".mxl" else "application/xml"
        return Response(result.read_bytes(),mimetype=mime)

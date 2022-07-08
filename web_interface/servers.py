from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import os

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def read_root():

    if os.path.exists('welcome.html'):
        fp = open('welcome.html', 'r')
        content = fp.read()
        fp.close()

    return content

@app.get("/run")
def read_item(lr: str|None = None, ul: str|None= None, vd: str|None= None,
              dicom_path: str|None= None, model_path: str|None= None,
              send_to_pacs: str|None= None, niftiz: str|None= None, 
              rescl: str|None= None, segm: str|None= None, rad: str|None= None,
               qct: str|None= None, out_path: str|None= None):

    adv =  do_work(lr, ul, vd, dicom_path, model_path, send_to_pacs, niftiz,
                  rescl, segm, rad, qct, out_path)

    #os.system("""echo "Hello world" """)

    return f"{adv}" 

def do_work(lr, ul, vd, dicom_path, model_path, send_to_pacs,
                  niftiz, rescl, segm, rad, qct, out_path):

    # sanity checks. do not start the pipeline if some args are invalid
    if not out_path or not os.path.isdir(out_path):
        return f'error with output path ({out_path})'
    elif not dicom_path or not os.path.isdir(dicom_path):
        return 'error with input path'
    elif not model_path or not os.path.isdir(model_path):
        return 'error with model path'

    args = f'--base_dir {dicom_path} --model {model_path} --output_dir {out_path} '
    if lr == 'on':
        args += '-lr '
    if ul == 'on':
        args += '-ul '
    if vd == 'on':
        args += '-vd '

    if not niftiz:
        args += '-n '
    if not rescl:
        args += '-r '
    if not segm:
        args += '-k '
    if not rad:
        args += '-e '
    if not qct:
        args += '-q '

    # still need to implement "send to pacs"
    cmd = f"covid-classifier {args}"
    os.system(cmd)
    return cmd


app.mount("/static", StaticFiles(directory="static"), name="static")
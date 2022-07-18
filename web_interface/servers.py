from ast import Return
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import time
import os

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def read_root():

    if os.path.exists('welcome.html'):
        fp = open('welcome.html', 'r')
        content = fp.read()
        fp.close()

    return content

@app.get("/run", response_class=HTMLResponse)
def read_item(background_tasks: BackgroundTasks, 
            dicom_path:   str|None = None, model_path: str|None = None,
            send_to_pacs: str|None = None, niftiz:     str|None = None, rescliso: str|None = None,
            lr:           str|None = None, ul:         str|None = None, vd:       str|None = None,
            rescl3:       str|None = None, segm:       str|None = None, rad:      str|None = None,
            qct:          str|None = None, out_path:   str|None = None, get_from_pacs: str|None = None,
            ip:           str|None = None, port:       str|None = None, aetitle:       str|None = None, 
            patientID:    str|None = None, seriesUID:  str|None = None, studyUID:      str|None = None,
            ):

    background_tasks.add_task(do_work_std, ip, port, aetitle, patientID, studyUID, seriesUID,
     dicom_path, model_path, out_path, lr, ul, vd, get_from_pacs, send_to_pacs,
    niftiz, segm, rescl3, rescliso, rad, qct)
  
    #log = do_work_std(ip, port, aetitle, patientID, studyUID, seriesUID,
    #    dicom_path, model_path, out_path, lr, ul, vd, get_from_pacs, send_to_pacs,
    #    niftiz, segm, rescl, rad, qct)

    if os.path.exists('goodbye.html'):
        fp = open('goodbye.html', 'r')
        out_msg = fp.read()
        out_msg= out_msg[:309] + '\n' + out_path + out_msg[309:]
        fp.close()
    return out_msg

    #return PDF

def do_work_std(ip, port, aetitle,
                    patientID, studyUID, seriesUID,
                    dicom_path, model_path, out_path, 
                    lr, ul, vd, 
                    get_from_pacs, send_to_pacs, 
                    niftiz, segm, rescl3, rescliso, rad, qct):

    args=''

    if get_from_pacs=='on':
        #sanity checks on secondary params
        if not ip or not port or not aetitle:
            return f"Error with ip {ip}, port {port} or AE Title {aetitle}"
        elif not patientID or not studyUID or not seriesUID:
            return f"Error with patient ID {patientID}, study UID {studyUID} or series UID {seriesUID}"

        try:
            port = int(port)
        except:
            return f"Could not convert port {port} to integer"

        args += f'--from_pacs --ip {ip} --port {port} --aetitle {aetitle} '
        args += f'--patientID {patientID} --seriesUID {seriesUID} --studyUID {studyUID} '

        if send_to_pacs=='Yes':
            args += '--to_pacs '
        print("Stll here")

    else:
        if send_to_pacs=='Yes':
            if not ip or not port or not aetitle:
                return f"Error with ip {ip}, port {port} or AE Title {aetitle}"
            try:
                port = int(port)
            except:
                return f"Could not convert port {port} to integer"
            args += f'--to_pacs --ip {ip} --port {port} --aetitle {aetitle} '

            
    
    # sanity checks. do not start the pipeline if some args are invalid
    if out_path is None:
        return f'error with output path ({out_path})'
    elif not os.path.isdir(out_path):
        os.mkdir(out_path)
        print(f"Created directory {out_path}")
    if not dicom_path:
        return f'error with input path {dicom_path}'
    elif not os.path.isdir(dicom_path):
        os.mkdir(dicom_path)
        print(f"Created directory {dicom_path}")
    elif not model_path or not os.path.isdir(model_path):
        return f'error with model path {model_path}'

    args += f'--base_dir {dicom_path} --model {model_path} --output_dir {out_path} '
    if lr == 'on':
        args += '-lr '
    if ul == 'on':
        args += '-ul '
    if vd == 'on':
        args += '-vd '

    if not niftiz:
        args += '-n '
    if not rescl3:
        args += '-r3 '
    if not rescliso:
        args+= '-ri '
    if not segm:
        args += '-k '
    if not rad:
        args += '-e '
    if not qct:
        args += '-q '

    # still need to implement "send to pacs"
    cmd = f"clearlung {args}"
    print(f"Now running command {cmd}")
    os.system(cmd)
    return cmd

app.mount("/static", StaticFiles(directory="static"), name="static")
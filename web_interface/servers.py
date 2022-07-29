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
            subroi:       str|None = None, rescl3:     str|None = None, segm:     str|None = None,
            radqct:       str|None = None, out_path:   str|None = None,
            get_from_pacs:str|None = None, ip:         str|None = None, port:     str|None = None,
            aetitle:      str|None = None, patientID:  str|None = None, seriesUID:str|None = None,
            studyUID:      str|None = None,single_mode:  str|None = None, tag:    str|None = None,
            GLCM_L: str|None=None, GLCM_R: str|None=None, GLCM_BW: str|None=None,
            GLSZM_L: str|None=None, GLSZM_R: str|None=None, GLSZM_BW: str|None=None,
            GLRLM_L: str|None=None, GLRLM_R: str|None=None, GLRLM_BW: str|None=None,
            NGTDM_L: str|None=None, NGTDM_R: str|None=None, NGTDM_BW: str|None=None,
            GLDM_L: str|None=None, GLDM_R: str|None=None, GLDM_BW: str|None=None,
            shape3D_L: str|None=None, shape3D_R: str|None=None, shape3D_BW: str|None=None,
            st_qct: str|None=None, st_iso: str|None=None, genpdf: str|None=None,
            ):

    background_tasks.add_task(do_work_std, ip, port, aetitle, patientID, studyUID, seriesUID,
     dicom_path, model_path, out_path, subroi, get_from_pacs, send_to_pacs,
     niftiz, segm, rescl3, rescliso, radqct, single_mode, tag, GLCM_L, GLCM_R, GLCM_BW,
     GLSZM_L, GLSZM_R, GLSZM_BW, GLRLM_L, GLRLM_R, GLRLM_BW,
     NGTDM_L, NGTDM_R, NGTDM_BW, GLDM_L, GLDM_R, GLDM_BW,
     shape3D_L, shape3D_R, shape3D_BW, st_qct, st_iso, genpdf)
  
    #log = do_work_std(ip, port, aetitle, patientID, studyUID, seriesUID,
    #    dicom_path, model_path, out_path, subroi, get_from_pacs, send_to_pacs,
    #    niftiz, segm, rescl, rad, qct, single_mode, tag)

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
                    subroi, get_from_pacs, send_to_pacs, 
                    niftiz, segm, rescl3, rescliso, radqct,
                    single_mode, tag, GLCM_L, GLCM_R, GLCM_BW,
                    GLSZM_L, GLSZM_R, GLSZM_BW, GLRLM_L, GLRLM_R, GLRLM_BW,
                    NGTDM_L, NGTDM_R, NGTDM_BW, GLDM_L, GLDM_R, GLDM_BW,
                    shape3D_L, shape3D_R, shape3D_BW,
                    st_qct, st_iso, genpdf):

   
    args=''

    if single_mode=='on':
        args += '--single '


    if get_from_pacs=='on':
        #sanity checks on secondary params
        if not ip or not port or not aetitle:
            print( f"Error with ip {ip}, port {port} or AE Title {aetitle}")
            return
        elif not patientID or not studyUID or not seriesUID:
            print(f"Error with patient ID {patientID}, study UID {studyUID} or series UID {seriesUID}")
            return
        try:
            port = int(port)
        except:
            print( f"Could not convert port {port} to integer")
            return

        args += f'--from_pacs --ip {ip} --port {port} --aetitle {aetitle} '
        args += f'--patientID {patientID} --seriesUID {seriesUID} --studyUID {studyUID} '

        if send_to_pacs=='Yes':
            args += '--to_pacs '

    else:
  
        if send_to_pacs=='Yes':
            if not ip or not port or not aetitle:
                return f"Error with ip {ip}, port {port} or AE Title {aetitle}"
            try:
                port = int(port)
            except:
                return f"Could not convert port {port} to integer"
            args += f'--to_pacs --ip {ip} --port {port} --aetitle {aetitle} '

    if subroi=='on':
        args += '--subroi ' 
    
    # sanity checks. do not start the pipeline if some args are invalid
    if out_path is None:
        print( f"Error with output path {out_path}")
        return f'error with output path ({out_path})'
    elif not os.path.isdir(out_path):
        os.mkdir(out_path)
        print(f"Created directory {out_path}")
    if not dicom_path:
        print( f'error with dicom path ({dicom_path})')
        return f'error with input path {dicom_path}'
    elif not os.path.isdir(dicom_path):
        os.mkdir(dicom_path)
        print(f"Created directory {dicom_path}")
    elif not model_path or not os.path.isdir(model_path):
        print(f"Error with model path {model_path}")
        return f'error with model path {model_path}'

    args += f'--base_dir {dicom_path} --model {model_path} --output_dir {out_path} --target_dir CT '

    if not niftiz:
        args += '-n '
    if not rescl3:
        args += '-r3 '
    if not rescliso:
        args+= '-ri '
    if not segm:
        args += '-k '
    if not radqct:
        args += '--radqct '
    if not genpdf:
        args += '--skippdf '

    if not st_qct or float(st_qct)<=0:
        print (f'error with qct slice thickness {st_qct}')
        return 
    
    if not st_iso or float(st_iso)<=0:
        print (f'error with iso slice thickness {st_iso}')
        return

    args += f'--slice_thickness_qct {st_qct} --slice_thickness_iso {st_iso} '

    # radiomic feature params
    args += f'--GLCM_params  {int(GLCM_L)} {int(GLCM_R)} {int(GLCM_BW)} '
    args += f'--GLSZM_params {int(GLSZM_L)} {int(GLSZM_R)} {int(GLSZM_BW)} '
    args += f'--GLRLM_params {int(GLRLM_L)} {int(GLRLM_R)} {int(GLRLM_BW)} '
    args += f'--NGTDM_params {int(NGTDM_L)} {int(NGTDM_R)} {int(NGTDM_BW)} '
    args += f'--GLDM_params  {int(GLDM_L)} {int(GLDM_R)} {int(GLDM_BW)} '
    args += f'--shape3D_params {int(shape3D_L)} {int(shape3D_R)} {int(shape3D_BW)} '

    if tag:
        args += f'--tag {tag} '

    cmd = f"clearlung {args}"
    print(f"Now running command {cmd}")
    os.system(cmd)
    return cmd

app.mount("/static", StaticFiles(directory="static"), name="static")
import pathlib
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
from typing import Union

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def read_root():

    html_wpath = os.path.join(pathlib.Path(__file__).parent.absolute(),'welcome.html')
    if os.path.exists(html_wpath):
        fp = open(html_wpath, 'r')
        content = fp.read()
        fp.close()

    return content

@app.get("/run", response_class=HTMLResponse)
def read_item(background_tasks: BackgroundTasks, 
            dicom_path:   Union[str,None] = None, model_path: Union[str,None] = None,
            send_to_pacs: Union[str,None] = None, niftiz:     Union[str,None] = None, rescliso: Union[str,None] = None,
            subroi:       Union[str,None] = None, rescl3:     Union[str,None] = None, segm:     Union[str,None] = None,
            radqct:       Union[str,None] = None, out_path:   Union[str,None] = None,
            get_from_pacs:Union[str,None] = None, ip:         Union[str,None] = None, port:     Union[str,None] = None,
            aetitle:      Union[str,None] = None, patientID:  Union[str,None] = None, seriesUID:Union[str,None] = None,
            studyUID:      Union[str,None] = None,single_mode:  Union[str,None] = None, tag:    Union[str,None] = None,
            GLCM_L: Union[str,None]=None, GLCM_R: Union[str,None]=None, GLCM_BW: Union[str,None]=None,
            GLSZM_L: Union[str,None]=None, GLSZM_R: Union[str,None]=None, GLSZM_BW: Union[str,None]=None,
            GLRLM_L: Union[str,None]=None, GLRLM_R: Union[str,None]=None, GLRLM_BW: Union[str,None]=None,
            NGTDM_L: Union[str,None]=None, NGTDM_R: Union[str,None]=None, NGTDM_BW: Union[str,None]=None,
            GLDM_L: Union[str,None]=None, GLDM_R: Union[str,None]=None, GLDM_BW: Union[str,None]=None,
            shape3D_L: Union[str,None]=None, shape3D_R: Union[str,None]=None, shape3D_BW: Union[str,None]=None,
            FORD_L: Union[str,None]=None, FORD_R: Union[str,None]=None, FORD_BW: Union[str,None]=None,
            st_qct: Union[str,None]=None, st_iso: Union[str,None]=None, genpdf: Union[str,None]=None,
            history: Union[str, None]=None, ford_on: Union[str, None]=None, glcm_on:Union[str, None]=None,
            glszm_on:Union[str, None]=None, glrlm_on:Union[str, None]=None, ngtdm_on:Union[str, None]=None,
            gldm_on:Union[str, None]=None, shape3d_on:Union[str, None]=None
            ):
    

    background_tasks.add_task(do_work_std, ip, port, aetitle, patientID, studyUID, seriesUID,
     dicom_path, model_path, out_path, subroi, get_from_pacs, send_to_pacs,
     niftiz, segm, rescl3, rescliso, radqct, single_mode, tag, GLCM_L, GLCM_R, GLCM_BW,
     GLSZM_L, GLSZM_R, GLSZM_BW, GLRLM_L, GLRLM_R, GLRLM_BW,
     NGTDM_L, NGTDM_R, NGTDM_BW, GLDM_L, GLDM_R, GLDM_BW,
     shape3D_L, shape3D_R, shape3D_BW,
     FORD_L, FORD_R, FORD_BW,
     st_qct, st_iso, genpdf, history,
     ford_on, glcm_on, glszm_on, glrlm_on, ngtdm_on,
     gldm_on, shape3d_on)
  
    html_gpath = os.path.join(pathlib.Path(__file__).parent.absolute(),'goodbye.html')
    if os.path.exists(html_gpath):
        fp = open(html_gpath, 'r')
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
                    FORD_L, FORD_R, FORD_BW,
                    st_qct, st_iso, genpdf, history,
                    ford_on, glcm_on, glszm_on, glrlm_on, ngtdm_on,
                    gldm_on, shape3d_on):

   
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
        try:
            os.mkdir(out_path)
            print(f"Created directory {out_path}")
        except FileNotFoundError:
            print("##########################")
            print(f"Results path '{out_path}' not found!!")
            print('##########################')
            return

    if not dicom_path:
        print( f'error with dicom path ({dicom_path})')
        return f'error with input path {dicom_path}'
    elif not os.path.isdir(dicom_path):
        try:
            os.mkdir(dicom_path)
            print(f"Created directory {dicom_path}")
        except FileNotFoundError:
            print("##########################")
            print(f"Input path '{dicom_path}' not found!!")
            print('##########################')
            return
    elif not model_path or not os.path.isdir(model_path):
        print(f"Error with model path {model_path}")
        return f'error with model path {model_path}'

    args += f'--base_dir {dicom_path} --model {model_path} --output_dir {out_path} --target_dir CT '
    if not history:
        print("History path missing!")
    args += f'--history_path {history} '

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

    ford = 1 if ford_on else 0
    glcm = 1 if glcm_on else 0
    glszm = 1 if glszm_on else 0
    glrlm = 1 if glrlm_on else 0
    ngtdm = 1 if ngtdm_on else 0
    gldm = 1 if gldm_on else 0
    shape3d = 1 if shape3d_on else 0

    # radiomic feature params
    args += f'--GLCM_params   {glcm} {int(GLCM_L)} {int(GLCM_R)} {int(GLCM_BW)} '
    args += f'--GLSZM_params  {glszm} {int(GLSZM_L)} {int(GLSZM_R)} {int(GLSZM_BW)} '
    args += f'--GLRLM_params  {glrlm} {int(GLRLM_L)} {int(GLRLM_R)} {int(GLRLM_BW)} '
    args += f'--NGTDM_params  {ngtdm} {int(NGTDM_L)} {int(NGTDM_R)} {int(NGTDM_BW)} '
    args += f'--GLDM_params   {gldm} {int(GLDM_L)} {int(GLDM_R)} {int(GLDM_BW)} '
    args += f'--shape3D_params {shape3d} {int(shape3D_L)} {int(shape3D_R)} {int(shape3D_BW)} '
    args += f'--FORD_params   {ford} {int(FORD_L)} {int(FORD_R)} {int(FORD_BW)} '

    if tag:
        args += f'--tag {tag} '

    cmd = f"clearlung {args}"
    print(f"Now running command {cmd}")
    os.system(cmd)
    return cmd

app.mount("/static", StaticFiles(directory=os.path.join(pathlib.Path(__file__).parent.absolute(),"static")), name="static")
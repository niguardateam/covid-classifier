"""Module to connect to PACS and download/upload dicom series"""

from glob import glob
import os, sys
import pathlib
import shutil
from numpy import absolute
from pydicom.dataset import Dataset

from pynetdicom import AE, evt, build_role, debug_logger
from pynetdicom.sop_class import (
                                  PatientRootQueryRetrieveInformationModelGet,
                                  CTImageStorage,
                                  Verification
                                  )
from pydicom.uid import ImplicitVRLittleEndian



class DicomLoader():
    """Class to handle incoming communications with PACS"""

    def __init__(self, ip_add, port, aetitle, patient_id, series_id, study_id, output_path):
        """
        Constructor for the DicomLoader class.

        :param ip_add: IP address of the PACS node
        :port: port of the PACS node
        :aetitle: AE title of the PACS node
        :patient_id: Patient ID of the CT o obe downloaded
        :series_id: Series UID of the CT
        :study_id: Study UID of the CT
        :output_path: Path to results folder
        """

        self.port = port
        self.ip_add = ip_add
        self.aetitle = aetitle

        #series data:
        self.patient_id = patient_id
        self.study_uid = study_id
        self.series_uid = series_id
        self.output_path = output_path


    def download(self,):
        """
        Download a CT series from a PACS node
        """
        #debug_logger()

        def handle_store(event):
            """Handle a C-STORE request event."""
            dataset = event.dataset
            dataset.file_meta = event.file_meta

            target_dir = os.path.join(self.output_path , dataset.PatientID)

            if not os.path.isdir(target_dir):
                print("Creating new dir " + target_dir)
                os.mkdir(os.path.join(target_dir))
                os.mkdir(os.path.join(target_dir, "CT"))

            # Save the dataset using the SOP Instance UID as the filename
            dataset.save_as(os.path.join(target_dir, "CT", dataset.SOPInstanceUID  + '.dcm'),
                       write_like_original=False)

            # Return a 'Success' status
            return 0x0000

        """Execute main method. It should be used to save a new series in the "base dir" of the pipeline."""
        handlers = [(evt.EVT_C_STORE, handle_store)]

        ae = AE(ae_title='KOBE_CT')

        ae.add_requested_context(Verification, ImplicitVRLittleEndian)
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelGet, ImplicitVRLittleEndian)
        ae.add_requested_context(CTImageStorage, ImplicitVRLittleEndian)


        # Create an SCP/SCU Role Selection Negotiation item for CT Image Storage
        role = build_role(CTImageStorage, scp_role=True)

        ds = Dataset()
        ds.QueryRetrieveLevel = 'SERIES'
        ds.PatientID = self.patient_id
        ds.StudyInstanceUID = self.study_uid
        ds.SeriesInstanceUID = self.series_uid

        # Associate with peer AE (PACS / myPACS)?
        assoc = ae.associate(addr= self.ip_add,
                            port = self.port, 
                            ae_title=self.aetitle,
                            ext_neg=[role],
                            evt_handlers=handlers)


        if assoc.is_established:
            # Use the C-GET service to send the identifier
            responses = assoc.send_c_get(ds, PatientRootQueryRetrieveInformationModelGet)
            for (status, _) in responses:
                if status:
                    pass#print(f'C-GET query status: 0x{status.Status:04x}')
                else:
                    print('Connection timed out, was aborted or received invalid response')

            assoc.release()
        else:
            print('Association rejected, aborted or never connected')


    def upload(self, files_to_send, our_aet= 'KOBE_CT'):
        """Upload encapsulated PDF reports to PACS
        :param files_to_send: List of encapsulated dcm files to upload
        """

        for file in files_to_send:
            cmd = f"python3 -m pynetdicom storescu {self.ip_add} {self.port} {file} " +\
                  f"-aet {our_aet} -aec {self.aetitle}"
            os.system(cmd)
        
    def move_to_analyzed(self,):
        """
        Move the recently processed folder to another directory.
        """
        data_path = str(pathlib.Path(self.output_path).absolute().resolve()) 
        if sys.platform == 'linux':
            analyzed_path = "/media/kobayashi/Archivio6T/CLEARLUNG/analyzed/"
        else:
            analyzed_path=os.path.join(pathlib.Path(data_path).parent.absolute().resolve(), 'analyzed/') 
        
        if not os.path.isdir(analyzed_path):
            os.mkdir(analyzed_path)
        #remove target dir if it already exists
        target_name = os.path.basename(os.path.normpath(data_path))
        if os.path.isdir(os.path.join(analyzed_path, target_name)):
            shutil.rmtree(os.path.join(analyzed_path, target_name))
        shutil.move(src=data_path,
                    dst=analyzed_path)
        print(f"Folder {data_path} moved to {analyzed_path}")
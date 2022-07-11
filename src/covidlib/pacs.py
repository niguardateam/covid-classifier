"""Module to connect to PACS and download/upload dicom series"""

import os
from pydicom.dataset import Dataset

from pynetdicom import AE, evt, build_role, debug_logger
from pynetdicom.sop_class import (
                                  PatientRootQueryRetrieveInformationModelGet,
                                  CTImageStorage,
                                  Verification
                                  )
from pydicom.uid import ImplicitVRLittleEndian



class DicomDownloader():
    """Class to handle incoming communications with PACS"""

    def __init__(self, ip_add, port, aetitle, patient_id, series_id, study_id, output_path):

        self.port = port#4096
        self.ip_add = ip_add#"10.1.4.217"
        self.aetitle = aetitle#"MYPACS"

        #series data:
        self.patient_id = patient_id#'30069281'
        self.study_uid = study_id#'1.2.840.113704.1.111.3032.1653547542.1'
        self.series_uid = series_id#'1.2.840.113704.1.111.3032.1653547763.23'
        self.output_path = output_path #'../output/'


    def run(self,):
        debug_logger()

        def handle_store(event):
            """Handle a C-STORE request event."""
            dataset = event.dataset
            dataset.file_meta = event.file_meta

            target_dir = os.path.join(self.output_path , dataset.PatientID)

            if not os.path.isdir(target_dir):
                print("Creating new dir " + target_dir)
                os.mkdir(os.path.join(self.output_path , dataset.PatientID))
                os.mkdir(os.path.join(self.output_path , dataset.PatientID, "CT"))

            # Save the dataset using the SOP Instance UID as the filename
            dataset.save_as(os.path.join(self.output_path ,  dataset.PatientID, "CT", dataset.SOPInstanceUID  + '.dcm'),
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
                    print(f'C-GET query status: 0x{status.Status:04x}')
                else:
                    print('Connection timed out, was aborted or received invalid response')

            assoc.release()
        else:
            print('Association rejected, aborted or never connected')


if __name__=="__main__":
    obj = DicomDownloader(
        ip_add="10.1.150.22", port=104,
        aetitle='EINIG', patient_id= '30368597',
        study_id= '2.25.75039712154566624178959761586824730424',
        series_id='1.3.12.2.1107.5.1.4.105451.30000022070908462527600000329',
        output_path="/home/kobayashi/Scrivania/andreasala/emg_try"
    )
    obj.run()

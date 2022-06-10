"""Module to connect to PACS and download/upload dicom series"""

from pydicom.dataset import Dataset

from pynetdicom import AE, evt, build_role, debug_logger
from pynetdicom.sop_class import (
                                  PatientRootQueryRetrieveInformationModelGet,
                                  CTImageStorage,
                                  Verification
                                  )

debug_logger()

class DicomDownloader():
    """Class to handle communications with PACS"""

    def __init__(self, ip_add, port, aetitle, patient_id, series_id, study_id, output_path):

        self.port = port#4096
        self.ip_add = ip_add#"10.1.4.217"
        self.aetitle = aetitle#"MYPACS"

        #series data:

        self.patient_id = patient_id#'30069281'
        self.study_id = study_id#'1.2.840.113704.1.111.3032.1653547542.1'
        self.series_id = series_id#'1.2.840.113704.1.111.3032.1653547763.23'

# output path:
        self.output_path = output_path #'../output/'

# Implement the handler for evt.EVT_C_STORE
    def handle_store(self,event):
        """Handle a C-STORE request event."""
        dataset = event.dataset
        dataset.file_meta = event.file_meta

        # Save the dataset using the SOP Instance UID as the filename
        dataset.save_as(self.output_path + 'CT_' + dataset.SOPInstanceUID  + '.dcm',
                   write_like_original=False)

        # Return a 'Success' status
        return 0x0000

    def run(self,):
        """Execute main method"""
        handlers = [(evt.EVT_C_STORE, self.handle_store)]

        app_ent = AE()

        app_ent.add_requested_context(Verification)
        app_ent.add_requested_context(PatientRootQueryRetrieveInformationModelGet)
        app_ent.add_requested_context(CTImageStorage)

        # Create an SCP/SCU Role Selection Negotiation item for CT Image Storage
        role = build_role(CTImageStorage, scp_role=True)

        dataset = Dataset()
        dataset.QueryRetrieveLevel = 'SERIES'
        dataset.PatientID = self.patient_id
        dataset.StudyInstanceUID = self.study_id
        dataset.SeriesInstanceUID = self.series_id

        # Associate with peer AE (PACS / myPACS)?
        assoc = app_ent.associate(self.ip_add,
                             self.port,
                             self.aetitle,
                             ext_neg=[role],
                             evt_handlers=handlers)

        if assoc.is_established:
            # Use the C-GET service to send the identifier
            responses = assoc.send_c_get(dataset, PatientRootQueryRetrieveInformationModelGet)
            for (status, _) in responses:
                if status:
                    print(f'C-GET query status: 0x{status.Status:04x}')
                else:
                    print('Connection timed out, was aborted or received invalid response')
            print("Dicom series correctly downloaded")

            assoc.release()
        else:
            print('Association rejected, aborted or never connected')
